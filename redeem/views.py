from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from hadiah.models import Hadiah

# ── R: Katalog Hadiah & Riwayat Redeem (Member) ─────────────────────────────
@require_http_methods(['GET'])
def member_redeem_list(request):
    # TODO: ganti dengan @login_required setelah auth jalan
    # Sementara karena dummy, pastikan ada role member
    today = timezone.now().date()
    
    # Hanya tampilkan hadiah yang masih dalam periode (valid_start_date s.d. program_end)
    katalog = Hadiah.objects.filter(valid_start_date__lte=today, program_end__gte=today).select_related('id_penyedia')
    
    # Gunakan session untuk menyimpan riwayat redeem sementara (karena belum boleh ubah models.py)
    if 'riwayat_redeem' not in request.session:
        request.session['riwayat_redeem'] = []
    
    riwayat = request.session['riwayat_redeem']
    
    # Dummy data context
    award_miles = 32000 # TODO: Ambil dari UserProfile.award_miles setelah nyambung DB beneran
    
    return render(request, 'redeem/member_redeem.html', {
        'katalog': katalog,
        'riwayat': reversed(riwayat), # Tampilkan terbaru di atas
        'award_miles': f"{award_miles:,}",
    })

# ── C: Redeem Hadiah (Member) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def member_redeem_create(request, kode_hadiah):
    hadiah = get_object_or_404(Hadiah, kode_hadiah=kode_hadiah)
    today = timezone.now().date()
    
    # Validasi 1: Hadiah masih valid?
    if today < hadiah.valid_start_date or today > hadiah.program_end:
        messages.error(request, f"Hadiah '{hadiah.nama}' sedang tidak berlaku.")
        return redirect('redeem:member_redeem_list')
        
    # Validasi 2: Award miles cukup?
    award_miles_member = 32000 # TODO: Ambil dari UserProfile (request.user.userprofile.award_miles)
    
    if award_miles_member < hadiah.miles:
        messages.error(request, f"Award miles Anda tidak mencukupi untuk redeem '{hadiah.nama}'.")
        return redirect('redeem:member_redeem_list')
        
    # TODO: Potong award miles member dan simpan ke tabel REDEEM di database (tunggu inspectdb)
    
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
