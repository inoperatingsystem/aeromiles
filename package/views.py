from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import connection, DatabaseError
from django.utils import timezone

# ── R: Katalog Package (Member) ─────────────────────────────
@login_required(login_url='main:login')
@require_http_methods(['GET'])
def member_package_list(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, harga_paket, jumlah_award_miles FROM aeromiles.award_miles_package ORDER BY jumlah_award_miles ASC')
        columns = [col[0] for col in cursor.description]
        packages = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for pkg in packages:
        pkg['harga_paket_str'] = f"{int(pkg['harga_paket']):,}"
        pkg['jumlah_award_miles_str'] = f"{pkg['jumlah_award_miles']:,}"

    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', [request.user.email])
        result = cursor.fetchone()
        award_miles = result[0] if result else 0

    return render(request, 'package/list.html', {
        'packages': packages,
        'award_miles': award_miles,
    })

# ── C: Beli Package (Member) ────────────────────────────────────────────────
@login_required(login_url='main:login')
@require_http_methods(['POST'])
def member_package_buy(request, id_paket):
    email_member = request.user.email
    waktu_sekarang = timezone.now()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT jumlah_award_miles FROM aeromiles.award_miles_package WHERE id = %s', [id_paket])
            paket_result = cursor.fetchone()

            if not paket_result:
                messages.error(request, "Paket tidak ditemukan.")
                return redirect('package:list')

            jumlah_award_miles = paket_result[0]

            cursor.execute(
                '''
                INSERT INTO aeromiles.member_award_miles_package (email_member, id_award_miles_package, timestamp)
                VALUES (%s, %s, %s)
                ''',
                [email_member, id_paket, waktu_sekarang]
            )

        success_msg = f"SUKSES: Pembelian package berhasil. Award miles dan total miles Anda bertambah {jumlah_award_miles} miles."
        messages.success(request, success_msg)

    except DatabaseError as e:
        error_msg = str(e).split('\n')[0].replace('ERROR:  ', '').strip()
        messages.error(request, error_msg)

    return redirect('package:list')