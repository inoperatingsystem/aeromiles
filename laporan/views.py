from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import connection
from main.utils import dictfetchall

# ── R: Laporan & Riwayat Transaksi (Staf) ─────────────────────────────
@require_http_methods(['GET'])
def laporan_list(request):
    # TODO: ganti dengan @login_required + pengecekan role staf
    
    # Ambil riwayat transaksi dari member
    riwayat = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                m.email as member_email,
                p.first_mid_name || ' ' || p.last_name as member_name,
                m.total_miles,
                m.award_miles
            FROM aeromiles.member m
            JOIN aeromiles.pengguna p ON m.email = p.email
            ORDER BY m.email
        """)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            riwayat.append(dict(zip(columns, row)))
    
    # Filter (optional)
    tipe_filter = request.GET.get('tipe', '')
    
    # Hitung stats dari member
    total_beredar = sum(m['total_miles'] for m in riwayat)
    total_award = sum(m['award_miles'] for m in riwayat)
    stats = {
        'total_beredar': f"{total_beredar:,}",
        'total_redeem': '0',  # TODO: hitung dari tabel REDEEM
        'total_klaim': '0',   # TODO: hitung dari tabel KLAIM
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
    messages.info(request, "Fitur delete belum diimplementasikan.")
    return redirect('laporan:list')
