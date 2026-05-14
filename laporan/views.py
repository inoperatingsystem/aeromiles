from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection

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
    
    # Ambil data member dengan top miles dari database
    top_members = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY m.total_miles DESC) as rank,
                p.first_mid_name || ' ' || p.last_name as member_name,
                m.email as member_email,
                m.total_miles,
                COUNT(*) as jumlah_transaksi
            FROM aeromiles.member m
            JOIN aeromiles.pengguna p ON m.email = p.email
            GROUP BY m.email, p.first_mid_name, p.last_name, m.total_miles
            ORDER BY m.total_miles DESC
            LIMIT 10
        """)
        columns = [col[0] for col in cursor.description]
        top_members = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Format top members
    for member in top_members:
        member['total_miles_str'] = f"{member['total_miles']:,}"
    
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
    
    return render(request, 'laporan/index.html', {
        'riwayat': riwayat,
        'top_members': top_members,
        'stats': stats,
        'tipe_filter': tipe_filter,
    })

# ── D: Hapus Riwayat (Staf) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def laporan_delete(request, transaksi_id):
    messages.info(request, "Fitur delete belum diimplementasikan.")
    return redirect('laporan:list')
