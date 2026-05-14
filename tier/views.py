from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection

TIER_BENEFITS = {
    'T1': {'keuntungan': ['Akumulasi miles dasar', 'Akses penawaran khusus member'], 'color': '#0dcaf0', 'bg_color': '#f8f9fa'},
    'T2': {'keuntungan': ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner'], 'color': '#adb5bd', 'bg_color': '#f8f9fa'},
    'T3': {'keuntungan': ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg'], 'color': '#ffc107', 'bg_color': '#fffdf5'},
    'T4': {'keuntungan': ['Bonus miles 100%', 'Upgrade gratis (subject to availability)', 'Akses lounge first class', 'Extra bagasi 20kg', 'Dedicated hotline'], 'color': '#212529', 'bg_color': '#f8f9fa'},
}

# ── R: Informasi Tier (Member) ─────────────────────────────
@login_required(login_url='main:login')
@require_http_methods(['GET'])
def member_tier_info(request):
    # Ambil data tier dari database
    with connection.cursor() as cursor:
        cursor.execute('SELECT id_tier, nama, minimal_frekuensi_terbang, minimal_tier_miles FROM aeromiles.tier ORDER BY minimal_tier_miles ASC')
        columns = [col[0] for col in cursor.description]
        tiers_raw = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Format tier dengan benefits
    tiers = []
    for tier in tiers_raw:
        tier_id = tier['id_tier']
        tier_data = {
            'id_tier': tier_id,
            'nama': tier['nama'],
            'minimal_frekuensi_terbang': tier['minimal_frekuensi_terbang'],
            'minimal_tier_miles': tier['minimal_tier_miles'],
            'minimal_tier_miles_str': f"{tier['minimal_tier_miles']:,}",
            **TIER_BENEFITS.get(tier_id, {'keuntungan': [], 'color': '#000000', 'bg_color': '#f8f9fa'})
        }
        tiers.append(tier_data)

    # Ambil tier member saat ini menggunakan authenticated user
    member_tier_data = None
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT m.id_tier, t.nama, m.award_miles FROM aeromiles.member m JOIN aeromiles.tier t ON m.id_tier = t.id_tier WHERE m.email = %s',
            [request.user.email]
        )
        result = cursor.fetchone()
        if result:
            columns = [col[0] for col in cursor.description]
            member_tier_data = dict(zip(columns, result))

    if member_tier_data:
        current_tier_nama = member_tier_data['nama']
        current_tier_miles = member_tier_data['award_miles']
    else:
        current_tier_nama = 'Blue'
        current_tier_miles = 0

    # Hitung progress ke tier berikutnya
    next_tier = None
    for t in tiers:
        if t['minimal_tier_miles'] > current_tier_miles:
            next_tier = t
            break

    if next_tier:
        progress_percentage = min(100, int((current_tier_miles / next_tier['minimal_tier_miles']) * 100))
    else:
        progress_percentage = 100

    return render(request, 'tier/info.html', {
        'tiers': tiers,
        'current_tier_nama': current_tier_nama,
        'current_tier_miles': f"{current_tier_miles:,}",
        'next_tier': next_tier,
        'progress_percentage': progress_percentage,
    })
