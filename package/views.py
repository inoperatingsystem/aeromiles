from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import connection

# ── R: Katalog Package (Member) ─────────────────────────────
@require_http_methods(['GET'])
def member_package_list(request):
    # TODO: ganti dengan @login_required setelah auth jalan
    
    # Ambil packages dari database
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, harga_paket, jumlah_award_miles FROM aeromiles.award_miles_package ORDER BY jumlah_award_miles ASC')
        columns = [col[0] for col in cursor.description]
        packages = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Format packages dengan currency display
    for pkg in packages:
        pkg['harga_paket_str'] = f"{int(pkg['harga_paket']):,}"
        pkg['jumlah_award_miles_str'] = f"{pkg['jumlah_award_miles']:,}"
    
    # Ambil award miles member
    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', ['member1@gmail.com'])
        result = cursor.fetchone()
        award_miles = result[0] if result else 0
    
    return render(request, 'package/list.html', {
        'packages': packages,
        'award_miles': award_miles,
    })

# ── C: Beli Package (Member) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def member_package_buy(request, id_paket):
    # Cari paket dari database
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, harga_paket, jumlah_award_miles FROM aeromiles.award_miles_package WHERE id = %s', [id_paket])
        result = cursor.fetchone()
        if not result:
            messages.error(request, "Paket tidak ditemukan.")
            return redirect('package:list')
        columns = [col[0] for col in cursor.description]
        paket = dict(zip(columns, result))
    
    # Ambil award miles member saat ini
    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', ['member1@gmail.com'])
        result = cursor.fetchone()
        current_miles = result[0] if result else 0
    
    # Update award miles member
    new_miles = current_miles + paket['jumlah_award_miles']
    with connection.cursor() as cursor:
        cursor.execute('UPDATE aeromiles.member SET award_miles = %s WHERE email = %s', [new_miles, 'member1@gmail.com'])
    
    messages.success(request, f"Berhasil membeli paket {paket['id']}. Award miles Anda bertambah {paket['jumlah_award_miles']:,}.")
    return redirect('package:list')
