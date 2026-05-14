from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection, DatabaseError
from hadiah.models import Hadiah

# ── R: Katalog Hadiah & Riwayat Redeem (Member) ─────────────────────────────
@login_required(login_url='main:login')
@require_http_methods(['GET'])
def member_redeem_list(request):
    katalog = Hadiah.objects.all().select_related('id_penyedia')

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT
                r.timestamp,
                h.nama as nama_hadiah,
                h.miles,
                h.kode_hadiah
            FROM aeromiles.redeem r
            JOIN aeromiles.hadiah h ON r.kode_hadiah = h.kode_hadiah
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        ''', [request.user.email])

        columns = [col[0] for col in cursor.description]
        riwayat = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for item in riwayat:
            item['waktu'] = item['timestamp'].strftime("%Y-%m-%d %H:%M")

    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', [request.user.email])
        result = cursor.fetchone()
        award_miles = result[0] if result else 0

    return render(request, 'redeem/member_redeem.html', {
        'katalog': katalog,
        'riwayat': riwayat,
        'award_miles': f"{award_miles:,}",
    })

# ── C: Redeem Hadiah (Member) ────────────────────────────────────────────────
@login_required(login_url='main:login')
@require_http_methods(['POST'])
def member_redeem_create(request, kode_hadiah):
    email_member = request.user.email
    waktu_sekarang = timezone.now()

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT nama, miles FROM aeromiles.hadiah WHERE kode_hadiah = %s', [kode_hadiah])
            hadiah_result = cursor.fetchone()

            if not hadiah_result:
                messages.error(request, "Hadiah tidak ditemukan.")
                return redirect('redeem:member_redeem_list')

            nama_hadiah, miles = hadiah_result

            cursor.execute(
                '''
                INSERT INTO aeromiles.redeem (email_member, kode_hadiah, timestamp)
                VALUES (%s, %s, %s)
                ''',
                [email_member, kode_hadiah, waktu_sekarang]
            )

        success_msg = f'SUKSES: Redeem hadiah "{nama_hadiah}" berhasil. Award miles Anda berkurang {miles} miles.'
        messages.success(request, success_msg)

    except DatabaseError as e:
        error_msg = str(e).split('\n')[0].replace('ERROR:  ', '').strip()
        messages.error(request, error_msg)

    return redirect('redeem:member_redeem_list')