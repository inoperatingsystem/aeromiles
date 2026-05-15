from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection
from main.utils import dictfetchall

def staf_required(view_func):
    """Decorator untuk memastikan user adalah staf yang terautentikasi."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('main:login')
        if not request.user.is_staf:
            messages.error(request, "Akses ditolak. Hanya staf yang dapat mengakses halaman ini.")
            return redirect('main:dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

# ── R: Laporan & Riwayat Transaksi (Staf) ─────────────────────────────
@staf_required
@require_http_methods(['GET'])
def laporan_list(request):
    
    # Ambil riwayat transaksi dari member
    riwayat = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                'Transfer' as tipe,
                p.first_mid_name || ' ' || p.last_name as member_name,
                m.email as member_email,
                t.jumlah as miles,
                t.timestamp as waktu,
                'Transfer|' || t.email_member_1 || '|' || t.email_member_2 || '|' || t.timestamp as id,
                true as can_delete
            FROM aeromiles.transfer t
            JOIN aeromiles.member m ON t.email_member_1 = m.email
            JOIN aeromiles.pengguna p ON m.email = p.email

            UNION ALL

            SELECT 
                'Redeem' as tipe,
                p.first_mid_name || ' ' || p.last_name as member_name,
                r.email_member as member_email,
                h.miles as miles,
                r.timestamp as waktu,
                'Redeem|' || r.email_member || '|' || r.kode_hadiah || '|' || r.timestamp as id,
                true as can_delete
            FROM aeromiles.redeem r
            JOIN aeromiles.hadiah h ON r.kode_hadiah = h.kode_hadiah
            JOIN aeromiles.member m ON r.email_member = m.email
            JOIN aeromiles.pengguna p ON m.email = p.email
            
            UNION ALL
            
            SELECT 
                'Package' as tipe,
                p.first_mid_name || ' ' || p.last_name as member_name,
                amp.email_member as member_email,
                a.jumlah_award_miles as miles,
                amp.timestamp as waktu,
                'Package|' || amp.id_award_miles_package || '|' || amp.email_member || '|' || amp.timestamp as id,
                true as can_delete
            FROM aeromiles.member_award_miles_package amp
            JOIN aeromiles.award_miles_package a ON amp.id_award_miles_package = a.id
            JOIN aeromiles.member m ON amp.email_member = m.email
            JOIN aeromiles.pengguna p ON m.email = p.email

            UNION ALL

            SELECT 
                'Klaim' as tipe,
                p.first_mid_name || ' ' || p.last_name as member_name,
                c.email_member as member_email,
                0 as miles,
                c.timestamp as waktu,
                'Klaim|' || CAST(c.id AS VARCHAR) as id,
                CASE WHEN c.status_penerimaan = 'Disetujui' THEN false ELSE true END as can_delete
            FROM aeromiles.claim_missing_miles c
            JOIN aeromiles.member m ON c.email_member = m.email
            JOIN aeromiles.pengguna p ON m.email = p.email

            ORDER BY waktu DESC
        """)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            riwayat.append(dict(zip(columns, row)))
    
    # Filter (optional)
    tipe_filter = request.GET.get('tipe', '')
    if tipe_filter:
        riwayat = [r for r in riwayat if r['tipe'] == tipe_filter]
    
    # Hitung stats total beredar dari tabel member
    with connection.cursor() as cursor:
        cursor.execute("SELECT COALESCE(SUM(total_miles), 0) FROM aeromiles.member")
        res = cursor.fetchone()
        total_beredar = res[0] if res else 0
    
    # Hitung total_redeem dari tabel REDEEM
    total_redeem = 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM aeromiles.redeem")
        result = cursor.fetchone()
        total_redeem = result[0] if result else 0
    
    # Hitung total_klaim dari tabel CLAIM_MISSING_MILES
    total_klaim = 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM aeromiles.claim_missing_miles")
        result = cursor.fetchone()
        total_klaim = result[0] if result else 0
    
    stats = {
        'total_beredar': f"{total_beredar:,}",
        'total_redeem': str(total_redeem),
        'total_klaim': str(total_klaim),
    }
    
    # Ambil Top 5 Members dari Stored Procedure
    top_members_db = []
    with connection.cursor() as cursor:
        if hasattr(connection.connection, 'notices'):
            del connection.connection.notices[:]
            
        cursor.execute("SELECT * FROM aeromiles.get_top_5_member()")
        rows = dictfetchall(cursor)
        
        # Tampilkan pesan dari Stored Procedure
        if hasattr(connection.connection, 'notices') and connection.connection.notices:
            for notice in connection.connection.notices:
                clean_notice = notice.replace('NOTICE:  ', '').strip()
                # Hindari pesan duplikat jika view dirender berulang kali
                if clean_notice not in [m.message for m in messages.get_messages(request)]:
                    messages.success(request, clean_notice)

        # Ubah format hasil query agar sesuai dengan template laporan
        for index, row in enumerate(rows):
            top_members_db.append({
                'rank': index + 1,
                'member_name': row['email'], # fallback ke email jika nama tidak diambil di SP
                'member_email': row['email'],
                'total_miles': f"{row['total_miles']:,}",
                'jumlah_transaksi': '-', # Karena SP tidak menghitung jumlah transaksi
            })

    return render(request, 'laporan/index.html', {
        'riwayat': riwayat,
        'top_members': top_members_db,
        'stats': stats,
        'tipe_filter': tipe_filter,
    })

# ── D: Hapus Riwayat (Staf) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def laporan_delete(request, transaksi_id):
    # Memecah composite ID yang digabungkan pakai separator '|' di SQL query
    parts = transaksi_id.split('|')
    tipe = parts[0]
    
    try:
        with connection.cursor() as cursor:
            if tipe == 'Transfer':
                cursor.execute("DELETE FROM aeromiles.transfer WHERE email_member_1 = %s AND email_member_2 = %s AND timestamp = %s", [parts[1], parts[2], parts[3]])
                messages.success(request, "Riwayat Transfer berhasil dihapus permanen.")
            
            elif tipe == 'Redeem':
                cursor.execute("DELETE FROM aeromiles.redeem WHERE email_member = %s AND kode_hadiah = %s AND timestamp = %s", [parts[1], parts[2], parts[3]])
                messages.success(request, "Riwayat Redeem berhasil dihapus permanen.")
            
            elif tipe == 'Package':
                cursor.execute("DELETE FROM aeromiles.member_award_miles_package WHERE id_award_miles_package = %s AND email_member = %s AND timestamp = %s", [parts[1], parts[2], parts[3]])
                messages.success(request, "Riwayat Pembelian Package berhasil dihapus permanen.")
            
            elif tipe == 'Klaim':
                # Validasi jika Disetujui
                cursor.execute("SELECT status_penerimaan FROM aeromiles.claim_missing_miles WHERE id = %s", [parts[1]])
                res = cursor.fetchone()
                if res and res[0] == 'Disetujui':
                    messages.error(request, "Gagal: Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.")
                else:
                    cursor.execute("DELETE FROM aeromiles.claim_missing_miles WHERE id = %s", [parts[1]])
                    messages.success(request, "Riwayat Klaim berhasil dihapus permanen.")
                    
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus data: {str(e)}")
        
    return redirect('laporan:list')