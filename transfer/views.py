from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection, transaction

def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def _get_current_member(request):
    if not request.user.is_authenticated:
        return None
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.email, COALESCE(m.award_miles, 0) 
            FROM MEMBER m 
            WHERE m.email = %s
        """, [request.user.email])
        row = cursor.fetchone()
        if row:
            from types import SimpleNamespace
            return SimpleNamespace(email_id=row[0], award_miles=row[1])
    return None

def transfer_list(request):
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    query = """
        SELECT t.email_member_1, t.email_member_2, t.timestamp, t.jumlah, t.catatan,
               p1.first_mid_name || ' ' || p1.last_name AS nama_pengirim,
               p2.first_mid_name || ' ' || p2.last_name AS nama_penerima
        FROM TRANSFER t
        LEFT JOIN PENGGUNA p1 ON t.email_member_1 = p1.email
        LEFT JOIN PENGGUNA p2 ON t.email_member_2 = p2.email
        WHERE t.email_member_1 = %s OR t.email_member_2 = %s
        ORDER BY t.timestamp DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [member.email_id, member.email_id])
        rows = _dictfetchall(cursor)

    transfers_data = []
    for t in rows:
        if t['email_member_1'] == member.email_id:
            tipe = 'Kirim'
            member_nama = t['nama_penerima'] if t['nama_penerima'] else t['email_member_2']
            member_email = t['email_member_2']
            jumlah_tampil = f"-{t['jumlah']}"
        else:
            tipe = 'Terima'
            member_nama = t['nama_pengirim'] if t['nama_pengirim'] else t['email_member_1']
            member_email = t['email_member_1']
            jumlah_tampil = f"+{t['jumlah']}"
            
        transfers_data.append({
            'waktu': t['timestamp'].strftime('%Y-%m-%d %H:%M') if t['timestamp'] else '',
            'nama': member_nama,
            'email': member_email,
            'jumlah': jumlah_tampil,
            'catatan': t['catatan'] or '-',
            'tipe': tipe
        })
    
    ctx = {
        'transfers': transfers_data,
        'award_miles': f"{(member.award_miles):,}",
        'role': 'member'
    }
    return render(request, 'transfer/list.html', ctx)


@require_http_methods(['POST'])
def transfer_create(request):
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('transfer:transfer_list')

    penerima_email = request.POST.get('penerima_email', '').strip()
    jumlah_miles_str = request.POST.get('jumlah_miles', '').strip()
    catatan = request.POST.get('catatan', '').strip()
    
    errors = []
    
    if not penerima_email:
        errors.append("Email penerima wajib diisi.")
    elif penerima_email == member.email_id:
        errors.append("Anda tidak dapat mentransfer miles ke diri sendiri.")
        
    jumlah_miles = 0
    if not jumlah_miles_str:
        errors.append("Jumlah miles wajib diisi.")
    else:
        try:
            jumlah_miles = int(jumlah_miles_str)
            if jumlah_miles <= 0:
                errors.append("Jumlah miles harus lebih dari 0.")
            elif jumlah_miles > member.award_miles:
                errors.append("Award miles tidak mencukupi.")
        except ValueError:
            errors.append("Jumlah miles tidak valid.")
            
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('transfer:transfer_list')
        
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM MEMBER WHERE email = %s", [penerima_email])
                if not cursor.fetchone():
                    messages.error(request, 'Email penerima belum terdaftar sebagai member.')
                    return redirect('transfer:transfer_list')

                cursor.execute("""
                    INSERT INTO TRANSFER (email_member_1, email_member_2, timestamp, jumlah, catatan)
                    VALUES (%s, %s, %s, %s, %s)
                """, [member.email_id, penerima_email, timezone.now(), jumlah_miles, catatan or None])
                
                cursor.execute("""
                    UPDATE MEMBER SET award_miles = COALESCE(award_miles, 0) - %s WHERE email = %s
                """, [jumlah_miles, member.email_id])
                
                cursor.execute("""
                    UPDATE MEMBER SET award_miles = COALESCE(award_miles, 0) + %s WHERE email = %s
                """, [jumlah_miles, penerima_email])
                
        messages.success(request, f"Berhasil mentransfer {jumlah_miles} miles ke {penerima_email}.")
    except Exception as e:
        messages.error(request, 'Terjadi kesalahan sistem dalam memproses transfer Anda.')

    return redirect('transfer:transfer_list')