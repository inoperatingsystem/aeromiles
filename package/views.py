from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone

# DUMMY DATA untuk AWARD_MILES_PACKAGE (karena models.py belum boleh dibuat)
# TODO: Ganti dengan query dari model AWARD_MILES_PACKAGE setelah inspectdb dijalankan
DUMMY_PACKAGES = [
    {
        'id': 'AMP-001',
        'jumlah_award_miles': '1,000',
        'harga_paket': '150,000',
    },
    {
        'id': 'AMP-002',
        'jumlah_award_miles': '5,000',
        'harga_paket': '650,000',
    },
    {
        'id': 'AMP-003',
        'jumlah_award_miles': '10,000',
        'harga_paket': '1,200,000',
    },
    {
        'id': 'AMP-004',
        'jumlah_award_miles': '25,000',
        'harga_paket': '2,750,000',
    },
]

# ── R: Katalog Package (Member) ─────────────────────────────
@require_http_methods(['GET'])
def member_package_list(request):
    # TODO: ganti dengan @login_required setelah auth jalan
    
    # Dummy data context
    award_miles = 32000 # TODO: Ambil dari UserProfile.award_miles setelah nyambung DB
    
    return render(request, 'package/list.html', {
        'packages': DUMMY_PACKAGES,
        'award_miles': award_miles,
    })

# ── C: Beli Package (Member) ────────────────────────────────────────────────
@require_http_methods(['POST'])
def member_package_buy(request, id_paket):
    # Cari paket dari dummy data
    # TODO: ganti dengan paket = get_object_or_404(AwardMilesPackage, id=id_paket)
    paket = next((p for p in DUMMY_PACKAGES if p['id'] == id_paket), None)
    
    if not paket:
        messages.error(request, "Paket tidak ditemukan.")
        return redirect('package:list')
        
    # TODO: Tambah award_miles member
    # user_profile = request.user.userprofile
    # user_profile.award_miles += paket['jumlah_award_miles']
    # user_profile.save()
    
    # TODO: Catat transaksi ke MEMBER_AWARD_MILES_PACKAGE di database
    # MemberAwardMilesPackage.objects.create(...)
    
    messages.success(request, f"Berhasil membeli paket {paket['id']}. Award miles Anda bertambah {paket['jumlah_award_miles']}.")
    return redirect('package:list')
