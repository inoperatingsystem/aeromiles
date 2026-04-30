from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# DUMMY DATA untuk tabel TIER (menunggu inspectdb)
DUMMY_TIERS = [
    {
        'id_tier': 'T-001',
        'nama': 'Blue',
        'minimal_frekuensi_terbang': 0,
        'minimal_tier_miles': 0,
        'minimal_tier_miles_str': '0',
        'keuntungan': [
            'Akumulasi miles dasar',
            'Akses penawaran khusus member'
        ],
        'color': '#0dcaf0', # info
        'bg_color': '#f8f9fa'
    },
    {
        'id_tier': 'T-002',
        'nama': 'Silver',
        'minimal_frekuensi_terbang': 10,
        'minimal_tier_miles': 15000,
        'minimal_tier_miles_str': '15,000',
        'keuntungan': [
            'Bonus miles 25%',
            'Priority check-in',
            'Akses lounge partner'
        ],
        'color': '#adb5bd', # secondary
        'bg_color': '#f8f9fa'
    },
    {
        'id_tier': 'T-003',
        'nama': 'Gold',
        'minimal_frekuensi_terbang': 25,
        'minimal_tier_miles': 40000,
        'minimal_tier_miles_str': '40,000',
        'keuntungan': [
            'Bonus miles 50%',
            'Priority boarding',
            'Akses lounge premium',
            'Extra bagasi 10kg'
        ],
        'color': '#ffc107', # warning
        'bg_color': '#fffdf5' # slightly yellow bg for highlight
    },
    {
        'id_tier': 'T-004',
        'nama': 'Platinum',
        'minimal_frekuensi_terbang': 50,
        'minimal_tier_miles': 80000,
        'minimal_tier_miles_str': '80,000',
        'keuntungan': [
            'Bonus miles 100%',
            'Upgrade gratis (subject to availability)',
            'Akses lounge first class',
            'Extra bagasi 20kg',
            'Dedicated hotline'
        ],
        'color': '#212529', # dark
        'bg_color': '#f8f9fa'
    },
]

# ── R: Informasi Tier (Member) ─────────────────────────────
@require_http_methods(['GET'])
def member_tier_info(request):
    # TODO: Ambil dari request.user.userprofile setelah auth aktif
    
    # Dummy current status for testing UI
    current_tier_nama = 'Gold'
    current_tier_miles = 45000
    
    # Calculate progress
    next_tier = None
    for t in DUMMY_TIERS:
        if t['minimal_tier_miles'] > current_tier_miles:
            next_tier = t
            break
            
    # Calculate percentage for progress bar
    if next_tier:
        progress_percentage = min(100, int((current_tier_miles / next_tier['minimal_tier_miles']) * 100))
    else:
        progress_percentage = 100
        
    return render(request, 'tier/info.html', {
        'tiers': DUMMY_TIERS,
        'current_tier_nama': current_tier_nama,
        'current_tier_miles': f"{current_tier_miles:,}",
        'next_tier': next_tier,
        'progress_percentage': progress_percentage,
    })
