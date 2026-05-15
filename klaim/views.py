from types import SimpleNamespace
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection

MASKAPAI_CHOICES = []
BANDARA_CHOICES = []
KELAS_CHOICES = [('Economy', 'Economy'), ('Business', 'Business'), ('First', 'First')]
from django.db import connection

def _dictfetchall(cursor):
    """Fungsi helper untuk mereturn dictionary dari raw SQL cursor."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def _context_base():
    with connection.cursor() as cursor:
        cursor.execute("SELECT kode_maskapai, nama_maskapai FROM MASKAPAI")
        maskapai_rows = cursor.fetchall()
        
        cursor.execute("SELECT iata_code, nama, kota FROM BANDARA")
        bandara_rows = cursor.fetchall()

    maskapai_list = [(code, f"{code} - {name}") for code, name in maskapai_rows]
    bandara_list = [(code, f"{code} - {name}, {kota}") for code, name, kota in bandara_rows]

    return {
        'maskapai_list': maskapai_list or MASKAPAI_CHOICES,
        'bandara_list': bandara_list or BANDARA_CHOICES,
        'kelas_list': KELAS_CHOICES,
    }

def _get_current_member(request):
    if not request.user.is_authenticated:
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT email FROM MEMBER WHERE email = %s", [request.user.email])
        row = cursor.fetchone()
        return SimpleNamespace(email_id=row[0]) if row else None

def _get_current_staf(request):
    if not request.user.is_authenticated:
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT email FROM STAF WHERE email = %s", [request.user.email])
        row = cursor.fetchone()
        return SimpleNamespace(email_id=row[0]) if row else None


# =============================================================================
# MEMBER VIEWS
# =============================================================================

def member_klaim_list(request):
    filter_status = request.GET.get('status', '')
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    query = """
        SELECT c.*, p.first_mid_name || ' ' || p.last_name AS nama_member
        FROM CLAIM_MISSING_MILES c
        LEFT JOIN PENGGUNA p ON c.email_member = p.email
        WHERE c.email_member = %s
    """
    params = [member.email_id]

    if filter_status:
        query += " AND c.status_penerimaan = %s"
        params.append(filter_status)

    query += " ORDER BY c.timestamp DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = _dictfetchall(cursor)

    klaim_list = []
    for row in rows:
        klaim_list.append(SimpleNamespace(
            no_klaim=row['id'],
            maskapai=row['maskapai'],
            bandara_asal=row['bandara_asal'],
            bandara_tujuan=row['bandara_tujuan'],
            tanggal_penerbangan=row['tanggal_penerbangan'],
            flight_number=row['flight_number'],
            kelas_kabin=row['kelas_kabin'],
            nomor_tiket=row['nomor_tiket'],
            pnr=row['pnr'],
            status=row['status_penerimaan'],
            tanggal_pengajuan=row['timestamp'],
            email_member=row['email_member'],
            nama_member=row['nama_member'],
            get_rute=f"{row['bandara_asal']} -> {row['bandara_tujuan']}",
        ))

    ctx = _context_base()
    ctx.update({
        'klaim_list': klaim_list,
        'filter_status': filter_status,
        'role': 'member',
    })
    return render(request, 'klaim/member_list.html', ctx)


@require_http_methods(['POST'])
def member_klaim_create(request):
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

    maskapai            = request.POST.get('maskapai', '').strip()
    bandara_asal        = request.POST.get('bandara_asal', '').strip()
    bandara_tujuan      = request.POST.get('bandara_tujuan', '').strip()
    tanggal_penerbangan = request.POST.get('tanggal_penerbangan', '').strip()
    flight_number       = request.POST.get('flight_number', '').strip()
    kelas_kabin         = request.POST.get('kelas_kabin', '').strip()
    nomor_tiket         = request.POST.get('nomor_tiket', '').strip()
    pnr                 = request.POST.get('pnr', '').strip()

    errors = []
    if not maskapai: errors.append('Maskapai wajib dipilih.')
    if not bandara_asal: errors.append('Bandara asal wajib dipilih.')
    if not bandara_tujuan: errors.append('Bandara tujuan wajib dipilih.')
    if bandara_asal and bandara_tujuan and bandara_asal == bandara_tujuan:
        errors.append('Bandara asal dan tujuan tidak boleh sama.')
    if not tanggal_penerbangan: errors.append('Tanggal penerbangan wajib diisi.')
    if not flight_number: errors.append('Flight number wajib diisi.')
    if not kelas_kabin: errors.append('Kelas kabin wajib dipilih.')
    if not nomor_tiket: errors.append('Nomor tiket wajib diisi.')
    if not pnr: errors.append('PNR wajib diisi.')

    with connection.cursor() as cursor:
        if maskapai:
            cursor.execute("SELECT 1 FROM MASKAPAI WHERE kode_maskapai = %s", [maskapai])
            if not cursor.fetchone(): errors.append('Maskapai tidak valid.')
        if bandara_asal:
            cursor.execute("SELECT 1 FROM BANDARA WHERE iata_code = %s", [bandara_asal])
            if not cursor.fetchone(): errors.append('Bandara asal tidak valid.')
        if bandara_tujuan:
            cursor.execute("SELECT 1 FROM BANDARA WHERE iata_code = %s", [bandara_tujuan])
            if not cursor.fetchone(): errors.append('Bandara tujuan tidak valid.')

        if flight_number and tanggal_penerbangan and nomor_tiket:
            cursor.execute("""
                SELECT 1 FROM CLAIM_MISSING_MILES 
                WHERE email_member=%s AND flight_number=%s AND tanggal_penerbangan=%s AND nomor_tiket=%s
            """, [member.email_id, flight_number, tanggal_penerbangan, nomor_tiket])
            if cursor.fetchone():
                errors.append('Klaim duplikat: penerbangan dengan data yang sama sudah pernah diajukan.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('klaim:member_list')

        cursor.execute("""
            INSERT INTO CLAIM_MISSING_MILES (
                email_member, maskapai, bandara_asal, bandara_tujuan, 
                tanggal_penerbangan, flight_number, kelas_kabin, nomor_tiket, 
                pnr, status_penerimaan, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu', %s)
        """, [
            member.email_id, maskapai, bandara_asal, bandara_tujuan, 
            tanggal_penerbangan, flight_number, kelas_kabin, nomor_tiket, 
            pnr, timezone.now()
        ])

    messages.success(request, 'Klaim berhasil diajukan dan sedang menunggu verifikasi.')
    return redirect('klaim:member_list')


@require_http_methods(['POST'])
def member_klaim_update(request, no_klaim):
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

    with connection.cursor() as cursor:
        cursor.execute("SELECT email_member, status_penerimaan FROM CLAIM_MISSING_MILES WHERE id = %s", [no_klaim])
        klaim_row = cursor.fetchone()

        if not klaim_row:
            messages.error(request, 'Klaim tidak ditemukan.')
            return redirect('klaim:member_list')
        
        email_member_db, status_penerimaan_db = klaim_row

        if email_member_db != member.email_id:
            messages.error(request, 'Akses ditolak.')
            return redirect('klaim:member_list')
        
        if status_penerimaan_db != 'Menunggu':
            messages.error(request, 'Hanya klaim berstatus Menunggu yang dapat diubah.')
            return redirect('klaim:member_list')

        maskapai            = request.POST.get('maskapai', '').strip()
        bandara_asal        = request.POST.get('bandara_asal', '').strip()
        bandara_tujuan      = request.POST.get('bandara_tujuan', '').strip()
        tanggal_penerbangan = request.POST.get('tanggal_penerbangan', '').strip()
        flight_number       = request.POST.get('flight_number', '').strip()
        kelas_kabin         = request.POST.get('kelas_kabin', '').strip()
        nomor_tiket         = request.POST.get('nomor_tiket', '').strip()
        pnr                 = request.POST.get('pnr', '').strip()

        cursor.execute("""
            UPDATE CLAIM_MISSING_MILES
            SET maskapai = %s, bandara_asal = %s, bandara_tujuan = %s, 
                tanggal_penerbangan = %s, flight_number = %s, kelas_kabin = %s, 
                nomor_tiket = %s, pnr = %s
            WHERE id = %s
        """, [
            maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan, 
            flight_number, kelas_kabin, nomor_tiket, pnr, no_klaim
        ])

    messages.success(request, f'Klaim {no_klaim} berhasil diperbarui.')
    return redirect('klaim:member_list')


@require_http_methods(['POST'])
def member_klaim_delete(request, no_klaim):
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

    with connection.cursor() as cursor:
        cursor.execute("SELECT email_member, status_penerimaan FROM CLAIM_MISSING_MILES WHERE id = %s", [no_klaim])
        klaim_row = cursor.fetchone()

        if not klaim_row:
            messages.error(request, 'Klaim tidak ditemukan.')
            return redirect('klaim:member_list')
            
        if klaim_row[0] != member.email_id:
            messages.error(request, 'Akses ditolak.')
            return redirect('klaim:member_list')
            
        if klaim_row[1] != 'Menunggu':
            messages.error(request, 'Hanya klaim berstatus Menunggu yang dapat dibatalkan.')
            return redirect('klaim:member_list')

        cursor.execute("DELETE FROM CLAIM_MISSING_MILES WHERE id = %s", [no_klaim])

    messages.success(request, f'Klaim {no_klaim} berhasil dibatalkan.')
    return redirect('klaim:member_list')


# =============================================================================
# STAF VIEWS
# =============================================================================

def staf_klaim_list(request):
    if not _get_current_staf(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    filter_status   = request.GET.get('status', '')
    filter_maskapai = request.GET.get('maskapai', '')
    filter_tanggal  = request.GET.get('tanggal', '')

    query = """
        SELECT c.*, p.first_mid_name || ' ' || p.last_name AS nama_member
        FROM CLAIM_MISSING_MILES c
        LEFT JOIN PENGGUNA p ON c.email_member = p.email
        WHERE 1=1
    """
    params = []

    if filter_status:
        query += " AND c.status_penerimaan = %s"
        params.append(filter_status)
    if filter_maskapai:
        query += " AND c.maskapai = %s"
        params.append(filter_maskapai)
    if filter_tanggal:
        query += " AND DATE(c.timestamp) = %s"
        params.append(filter_tanggal)

    query += " ORDER BY c.timestamp DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = _dictfetchall(cursor)

    klaim_list = []
    for row in rows:
        klaim_list.append(SimpleNamespace(
            no_klaim=row['id'],
            maskapai=row['maskapai'],
            bandara_asal=row['bandara_asal'],
            bandara_tujuan=row['bandara_tujuan'],
            tanggal_penerbangan=row['tanggal_penerbangan'],
            flight_number=row['flight_number'],
            kelas_kabin=row['kelas_kabin'],
            nomor_tiket=row['nomor_tiket'],
            pnr=row['pnr'],
            status=row['status_penerimaan'],
            tanggal_pengajuan=row['timestamp'],
            email_member=row['email_member'],
            nama_member=row['nama_member'],
            get_rute=f"{row['bandara_asal']} -> {row['bandara_tujuan']}",
        ))

    ctx = _context_base()
    ctx.update({
        'klaim_list':      klaim_list,
        'filter_status':   filter_status,
        'filter_maskapai': filter_maskapai,
        'filter_tanggal':  filter_tanggal,
    })
    return render(request, 'klaim/staf_list.html', ctx)


@require_http_methods(['POST'])
def staf_klaim_action(request, no_klaim):
    staf = _get_current_staf(request)
    if not staf:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    action = request.POST.get('action')

    with connection.cursor() as cursor:
        cursor.execute("SELECT status_penerimaan FROM CLAIM_MISSING_MILES WHERE id = %s", [no_klaim])
        klaim_row = cursor.fetchone()

        
        if not klaim_row:
            messages.error(request, 'Klaim tidak ditemukan.')
            return redirect('klaim:staf_list')

        if klaim_row[0] != 'Menunggu':
            messages.error(request, f'Klaim {no_klaim} sudah diproses sebelumnya.')
            return redirect('klaim:staf_list')

        if action == 'setujui':
            if hasattr(connection.connection, 'notices'):
                del connection.connection.notices[:]
                
            cursor.execute("""
                UPDATE CLAIM_MISSING_MILES 
                SET status_penerimaan = 'Disetujui', email_staf = %s 
                WHERE id = %s
            """, [staf.email_id, no_klaim])
            
            if hasattr(connection.connection, 'notices') and connection.connection.notices:
                for notice in connection.connection.notices:
                    clean_notice = notice.replace('NOTICE:  ', '').strip()
                    messages.success(request, clean_notice)
            else:
                messages.success(request, f'Klaim {no_klaim} berhasil disetujui.')
        elif action == 'tolak':
            cursor.execute("""
                UPDATE CLAIM_MISSING_MILES 
                SET status_penerimaan = 'Ditolak', email_staf = %s 
                WHERE id = %s
            """, [staf.email_id, no_klaim])
            messages.error(request, f'Klaim {no_klaim} telah ditolak.')
        
    return redirect('klaim:staf_list')