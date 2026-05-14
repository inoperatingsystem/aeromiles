from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection
from hadiah.models import Hadiah

# ── R: Katalog Hadiah & Riwayat Redeem (Member) ─────────────────────────────
@require_http_methods(['GET'])
def member_redeem_list(request):
    # TODO: ganti dengan @login_required setelah auth jalan
    today = timezone.now().date()
    
    # Ambil hadiah aktif dari database
    katalog = Hadiah.objects.filter(valid_start_date__lte=today, program_end__gte=today).select_related('id_penyedia')
    
    # Gunakan session untuk menyimpan riwayat redeem sementara
    if 'riwayat_redeem' not in request.session:
        request.session['riwayat_redeem'] = []
    
    riwayat = request.session['riwayat_redeem']
    
    # Ambil award miles member dari database
    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', ['member1@gmail.com'])
        result = cursor.fetchone()
        award_miles = result[0] if result else 0
    
    return render(request, 'redeem/member_redeem.html', {
        'katalog': katalog,
        'riwayat': reversed(riwayat),
        'award_miles': f"{award_miles:,}",
    })

# ── C: Redeem Hadiah (Member) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def member_redeem_create(request, kode_hadiah):
    hadiah = Hadiah.objects.get(kode_hadiah=kode_hadiah) if Hadiah.objects.filter(kode_hadiah=kode_hadiah).exists() else None
    if not hadiah:
        messages.error(request, "Hadiah tidak ditemukan.")
        return redirect('redeem:member_redeem_list')
    
    today = timezone.now().date()
    
    # Validasi 1: Hadiah masih valid?
    if today < hadiah.valid_start_date or today > hadiah.program_end:
        messages.error(request, f"Hadiah '{hadiah.nama}' sedang tidak berlaku.")
        return redirect('redeem:member_redeem_list')
    
    # Ambil award miles member dari database
    with connection.cursor() as cursor:
        cursor.execute('SELECT award_miles FROM aeromiles.member WHERE email = %s', ['member1@gmail.com'])
        result = cursor.fetchone()
        award_miles_member = result[0] if result else 0
    
    # Validasi 2: Award miles cukup?
    if award_miles_member < hadiah.miles:
        messages.error(request, f"Award miles Anda tidak mencukupi untuk redeem '{hadiah.nama}'.")
        return redirect('redeem:member_redeem_list')
    
    # Update award miles member di database
    new_award_miles = award_miles_member - hadiah.miles
    with connection.cursor() as cursor:
        cursor.execute('UPDATE aeromiles.member SET award_miles = %s WHERE email = %s', [new_award_miles, 'member1@gmail.com'])
    
    # Simpan ke session untuk dummy UI
    riwayat = request.session.get('riwayat_redeem', [])
    waktu_sekarang = timezone.now().strftime("%Y-%m-%d %H:%M")
    
    transaksi = {
        'nama_hadiah': hadiah.nama,
        'kode_hadiah': hadiah.kode_hadiah,
        'waktu': waktu_sekarang,
        'miles': hadiah.miles,
    }
    
    riwayat.append(transaksi)
    request.session['riwayat_redeem'] = riwayat
    request.session.modified = True
    
    messages.success(request, f"Berhasil melakukan redeem '{hadiah.nama}'. Miles terpotong {hadiah.miles:,}.")
    return redirect('redeem:member_redeem_list')
