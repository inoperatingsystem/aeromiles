from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import uuid

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
        'status': 'Disetujui',
        'can_delete': False,  # Klaim yang disetujui tidak dapat dihapus
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


def _is_approved_missing_miles(transaksi):
    return transaksi.get('tipe') == 'Klaim' and transaksi.get('status') == 'Disetujui'


def _can_delete_transaction(transaksi):
    if 'can_delete' in transaksi:
        return transaksi['can_delete']
    return not _is_approved_missing_miles(transaksi)


def _prepare_riwayat(riwayat):
    prepared = []
    for transaksi in riwayat:
        item = dict(transaksi)
        item['can_delete'] = _can_delete_transaction(item)
        prepared.append(item)
    return prepared


def _delete_error_message(transaksi):
    if _is_approved_missing_miles(transaksi):
        return 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.'
    return 'Riwayat ini tidak dapat dihapus.'

TOP_MEMBERS = [
    {
        'rank': 1,
        'member_name': 'John W. Doe',
        'member_email': 'john@example.com',
        'total_miles': '18,000',
        'jumlah_transaksi': 3,
    },
    {
        'rank': 2,
        'member_name': 'Jane Smith',
        'member_email': 'jane@example.com',
        'total_miles': '5,000',
        'jumlah_transaksi': 1,
    },
    {
        'rank': 3,
        'member_name': 'Budi A. Santoso',
        'member_email': 'budi@example.com',
        'total_miles': '4,500',
        'jumlah_transaksi': 2,
    },
]

# ── R: Laporan & Riwayat Transaksi (Staf) ─────────────────────────────
@require_http_methods(['GET'])
def laporan_list(request):
    # TODO: ganti dengan @login_required + pengecekan role staf
    
    # Ambil transaksi dari session untuk dummy hapus-hapus
    if 'riwayat_staf' not in request.session:
        request.session['riwayat_staf'] = INITIAL_TRANSACTIONS

    riwayat = _prepare_riwayat(request.session['riwayat_staf'])
    
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
    
    return render(request, 'laporan/index.html', {
        'riwayat': riwayat,
        'top_members': TOP_MEMBERS,
        'stats': stats,
        'tipe_filter': tipe_filter,
    })

# ── D: Hapus Riwayat (Staf) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def laporan_delete(request, transaksi_id):
    riwayat = request.session.get('riwayat_staf', [])
    transaksi = next((r for r in riwayat if r['id'] == str(transaksi_id)), None)

    if transaksi:
        if not _can_delete_transaction(transaksi):
            messages.error(request, _delete_error_message(transaksi))
        else:
            request.session['riwayat_staf'] = [r for r in riwayat if r['id'] != str(transaksi_id)]
            request.session.modified = True
            messages.success(
                request,
                f"Riwayat {transaksi['tipe']} dari {transaksi['member_name']} berhasil dihapus.",
            )
    else:
        messages.error(request, 'Riwayat tidak ditemukan.')

    return redirect('laporan:list')
