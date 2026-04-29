from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Klaim, MASKAPAI_CHOICES, BANDARA_CHOICES, KELAS_CHOICES, generate_no_klaim


def _context_base():
    return {
        'maskapai_list': MASKAPAI_CHOICES,
        'bandara_list':  BANDARA_CHOICES,
        'kelas_list':    KELAS_CHOICES,
    }

# =============================================================================
# MEMBER VIEWS
# =============================================================================

def member_klaim_list(request):
    """Member melihat riwayat klaim miles"""
    filter_status = request.GET.get('status', '')
    qs = Klaim.objects.all() # Dummy mode: Anggap semua klaim punya member ini dulu
    
    if filter_status:
        qs = qs.filter(status=filter_status)

    ctx = _context_base()
    ctx.update({
        'klaim_list':    qs,
        'filter_status': filter_status,
        'role': 'member', # Untuk base_member.html nantinya
    })
    return render(request, 'klaim/member_list.html', ctx)


@require_http_methods(['POST'])
def member_klaim_create(request):
    """Member mengajukan klaim baru"""
    maskapai            = request.POST.get('maskapai', '').strip()
    bandara_asal        = request.POST.get('bandara_asal', '').strip()
    bandara_tujuan      = request.POST.get('bandara_tujuan', '').strip()
    tanggal_penerbangan = request.POST.get('tanggal_penerbangan', '').strip()
    flight_number       = request.POST.get('flight_number', '').strip()
    kelas_kabin         = request.POST.get('kelas_kabin', '').strip()
    nomor_tiket         = request.POST.get('nomor_tiket', '').strip()
    pnr                 = request.POST.get('pnr', '').strip()

    errors = []
    if not maskapai:            errors.append('Maskapai wajib dipilih.')
    if not bandara_asal:        errors.append('Bandara asal wajib dipilih.')
    if not bandara_tujuan:      errors.append('Bandara tujuan wajib dipilih.')
    if bandara_asal and bandara_tujuan and bandara_asal == bandara_tujuan:
        errors.append('Bandara asal dan tujuan tidak boleh sama.')
    if not tanggal_penerbangan: errors.append('Tanggal penerbangan wajib diisi.')
    if not flight_number:       errors.append('Flight number wajib diisi.')
    if not kelas_kabin:         errors.append('Kelas kabin wajib dipilih.')
    if not nomor_tiket:         errors.append('Nomor tiket wajib diisi.')
    if not pnr:                 errors.append('PNR wajib diisi.')

    # Cek duplikat
    if flight_number and tanggal_penerbangan and nomor_tiket:
        if Klaim.objects.filter(
            flight_number=flight_number,
            tanggal_penerbangan=tanggal_penerbangan,
            nomor_tiket=nomor_tiket
        ).exists():
            errors.append('Klaim duplikat: penerbangan dengan data yang sama sudah pernah diajukan.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('klaim:member_list')

    no = generate_no_klaim()
    Klaim.objects.create(
        no_klaim=no, maskapai=maskapai,
        bandara_asal=bandara_asal, bandara_tujuan=bandara_tujuan,
        tanggal_penerbangan=tanggal_penerbangan, flight_number=flight_number,
        kelas_kabin=kelas_kabin, nomor_tiket=nomor_tiket, pnr=pnr,
        nama_member="John Doe", email_member="john@example.com" # Dummy member
    )
    messages.success(request, f'Klaim {no} berhasil diajukan dan sedang menunggu verifikasi.')
    return redirect('klaim:member_list')


@require_http_methods(['POST'])
def member_klaim_update(request, no_klaim):
    """Member mengubah klaim yang berstatus Menunggu"""
    klaim = get_object_or_404(Klaim, no_klaim=no_klaim)
    if klaim.status != 'Menunggu':
        messages.error(request, 'Hanya klaim berstatus Menunggu yang dapat diubah.')
        return redirect('klaim:member_list')

    maskapai            = request.POST.get('maskapai', '').strip()
    bandara_asal        = request.POST.get('bandara_asal', '').strip()
    bandara_tujuan      = request.POST.get('bandara_tujuan', '').strip()
    tanggal_penerbangan = request.POST.get('tanggal_penerbangan', '').strip()
    flight_number       = request.POST.get('flight_number', '').strip()
    kelas_kabin         = request.POST.get('kelas_kabin', '').strip()
    nomor_tiket         = request.POST.get('nomor_tiket', '').strip()
    pnr                 = request.POST.get('pnr', '').strip()

    klaim.maskapai            = maskapai
    klaim.bandara_asal        = bandara_asal
    klaim.bandara_tujuan      = bandara_tujuan
    klaim.tanggal_penerbangan = tanggal_penerbangan
    klaim.flight_number       = flight_number
    klaim.kelas_kabin         = kelas_kabin
    klaim.nomor_tiket         = nomor_tiket
    klaim.pnr                 = pnr
    klaim.save()

    messages.success(request, f'Klaim {no_klaim} berhasil diperbarui.')
    return redirect('klaim:member_list')


@require_http_methods(['POST'])
def member_klaim_delete(request, no_klaim):
    """Member membatalkan klaim"""
    klaim = get_object_or_404(Klaim, no_klaim=no_klaim)
    if klaim.status != 'Menunggu':
        messages.error(request, 'Hanya klaim berstatus Menunggu yang dapat dibatalkan.')
        return redirect('klaim:member_list')
    klaim.delete()
    messages.success(request, f'Klaim {no_klaim} berhasil dibatalkan.')
    return redirect('klaim:member_list')


# =============================================================================
# STAF VIEWS
# =============================================================================

def staf_klaim_list(request):
    """Staf mengelola semua klaim missing miles"""
    filter_status   = request.GET.get('status', '')
    filter_maskapai = request.GET.get('maskapai', '')
    filter_tanggal  = request.GET.get('tanggal', '')

    qs = Klaim.objects.all().order_by('-tanggal_pengajuan')
    
    if filter_status:
        qs = qs.filter(status=filter_status)
    if filter_maskapai:
        qs = qs.filter(maskapai=filter_maskapai)
    if filter_tanggal:
        qs = qs.filter(tanggal_pengajuan__date=filter_tanggal)

    ctx = _context_base()
    ctx.update({
        'klaim_list':      qs,
        'filter_status':   filter_status,
        'filter_maskapai': filter_maskapai,
        'filter_tanggal':  filter_tanggal,
    })
    return render(request, 'klaim/staf_list.html', ctx)


@require_http_methods(['POST'])
def staf_klaim_action(request, no_klaim):
    """Staf menyetujui atau menolak klaim"""
    klaim = get_object_or_404(Klaim, no_klaim=no_klaim)
    action = request.POST.get('action') # 'setujui' atau 'tolak'
    
    if klaim.status != 'Menunggu':
        messages.error(request, f'Klaim {no_klaim} sudah diproses sebelumnya.')
        return redirect('klaim:staf_list')

    if action == 'setujui':
        klaim.status = 'Disetujui'
        klaim.email_staf = 'staf@aeromiles.com' # Dummy staf email
        klaim.save()
        messages.success(request, f'Klaim {no_klaim} berhasil disetujui.')
    elif action == 'tolak':
        klaim.status = 'Ditolak'
        klaim.email_staf = 'staf@aeromiles.com' # Dummy staf email
        klaim.save()
        messages.error(request, f'Klaim {no_klaim} telah ditolak.')
        
    return redirect('klaim:staf_list')
