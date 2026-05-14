from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import uuid
from django.db import connection
from main.utils import dictfetchall

# DUMMY DATA untuk Laporan & Riwayat (Karena belum ada model gabungan/logs)
INITIAL_TRANSACTIONS = [
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Transfer',
        'member_name': 'John W. Doe',
        'member_email': 'john@example.com',
        'miles': -5000,
        'waktu': '2025-01-15 10:30',
        'can_delete': True,
    },
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Redeem',
        'member_name': 'John W. Doe',
        'member_email': 'john@example.com',
        'miles': -3000,
        'waktu': '2025-01-20 16:00',
        'can_delete': True,
    },
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Package',
        'member_name': 'Jane Smith',
        'member_email': 'jane@example.com',
        'miles': 5000,
        'waktu': '2025-02-01 09:15',
        'can_delete': True,
    },
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Klaim',
        'member_name': 'Budi A. Santoso',
        'member_email': 'budi@example.com',
        'miles': 2500,
        'waktu': '2025-02-05 11:45',
        'can_delete': False, # Klaim yang disetujui tidak dapat dihapus
    },
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Transfer',
        'member_name': 'Budi A. Santoso',
        'member_email': 'budi@example.com',
        'miles': -2000,
        'waktu': '2025-02-10 14:00',
        'can_delete': True,
    },
    {
        'id': str(uuid.uuid4()),
        'tipe': 'Package',
        'member_name': 'John W. Doe',
        'member_email': 'john@example.com',
        'miles': 10000,
        'waktu': '2025-03-01 08:00',
        'can_delete': True,
    },
]

# TOP_MEMBERS di-fetch dinamis dari database

# ── R: Laporan & Riwayat Transaksi (Staf) ─────────────────────────────
@require_http_methods(['GET'])
def laporan_list(request):
    # TODO: ganti dengan @login_required + pengecekan role staf
    
    # Ambil transaksi dari session untuk dummy hapus-hapus
    if 'riwayat_staf' not in request.session:
        request.session['riwayat_staf'] = INITIAL_TRANSACTIONS
        
    riwayat = request.session['riwayat_staf']
    
    # Filter
    tipe_filter = request.GET.get('tipe', '')
    if tipe_filter:
        riwayat = [r for r in riwayat if r['tipe'].lower() == tipe_filter.lower()]
        
    # Stats (Dummy static for now, in real life you aggregate)
    stats = {
        'total_beredar': '27,500',
        'total_redeem': '3,000',
        'total_klaim': '2,500',
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
    if 'riwayat_staf' in request.session:
        riwayat = request.session['riwayat_staf']
        
        # Cari transaksi
        transaksi = next((r for r in riwayat if r['id'] == str(transaksi_id)), None)
        
        if transaksi:
            if not transaksi['can_delete']:
                messages.error(request, "Riwayat ini tidak dapat dihapus.")
            else:
                riwayat = [r for r in riwayat if r['id'] != str(transaksi_id)]
                request.session['riwayat_staf'] = riwayat
                request.session.modified = True
                messages.success(request, f"Riwayat {transaksi['tipe']} dari {transaksi['member_name']} berhasil dihapus.")
        else:
            messages.error(request, "Riwayat tidak ditemukan.")
            
    return redirect('laporan:list')
