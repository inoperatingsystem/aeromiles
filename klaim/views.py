from types import SimpleNamespace

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from main.models import Bandara, Maskapai, Member, Staf
from .models import Klaim, MASKAPAI_CHOICES, BANDARA_CHOICES, KELAS_CHOICES
from django.db import connection


def _context_base():
    maskapai_rows = list(Maskapai.objects.all().values_list('kode_maskapai', 'nama_maskapai'))
    bandara_rows = list(Bandara.objects.all().values_list('iata_code', 'nama', 'kota'))

    maskapai_list = [(code, f"{code} - {name}") for code, name in maskapai_rows]
    bandara_list = [(code, f"{code} - {name}, {kota}") for code, name, kota in bandara_rows]

    if not maskapai_list:
        maskapai_list = MASKAPAI_CHOICES
    if not bandara_list:
        bandara_list = BANDARA_CHOICES

    return {
        'maskapai_list': maskapai_list,
        'bandara_list': bandara_list,
        'kelas_list': KELAS_CHOICES,
    }


def _get_current_member(request):
    if not request.user.is_authenticated:
        return None
    return Member.objects.filter(email_id=request.user.email).select_related('email').first()


def _get_current_staf(request):
    if not request.user.is_authenticated:
        return None
    return Staf.objects.filter(email_id=request.user.email).select_related('email').first()


def _to_klaim_view(klaim):
    email_member = klaim.email_member
    nama_member = email_member.email.full_name if email_member and email_member.email else ''
    return SimpleNamespace(
        no_klaim=klaim.id,
        maskapai=klaim.maskapai_id,
        bandara_asal=klaim.bandara_asal_id,
        bandara_tujuan=klaim.bandara_tujuan_id,
        tanggal_penerbangan=klaim.tanggal_penerbangan,
        flight_number=klaim.flight_number,
        kelas_kabin=klaim.kelas_kabin,
        nomor_tiket=klaim.nomor_tiket,
        pnr=klaim.pnr,
        status=klaim.status_penerimaan,
        tanggal_pengajuan=klaim.timestamp,
        email_member=klaim.email_member_id,
        nama_member=nama_member,
        get_rute=f"{klaim.bandara_asal_id} -> {klaim.bandara_tujuan_id}",
    )

# =============================================================================
# MEMBER VIEWS
# =============================================================================

def member_klaim_list(request):
    """Member melihat riwayat klaim miles"""
    filter_status = request.GET.get('status', '')
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    qs = Klaim.objects.filter(email_member=member).order_by('-timestamp')

    if filter_status:
        qs = qs.filter(status_penerimaan=filter_status)

    ctx = _context_base()
    ctx.update({
        'klaim_list':    [_to_klaim_view(k) for k in qs],
        'filter_status': filter_status,
        'role': 'member', # Untuk base_member.html nantinya
    })
    return render(request, 'klaim/member_list.html', ctx)


@require_http_methods(['POST'])
def member_klaim_create(request):
    """Member mengajukan klaim baru"""
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

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

    if maskapai and not Maskapai.objects.filter(kode_maskapai=maskapai).exists():
        errors.append('Maskapai tidak valid.')
    if bandara_asal and not Bandara.objects.filter(iata_code=bandara_asal).exists():
        errors.append('Bandara asal tidak valid.')
    if bandara_tujuan and not Bandara.objects.filter(iata_code=bandara_tujuan).exists():
        errors.append('Bandara tujuan tidak valid.')

    # Cek duplikat
    if flight_number and tanggal_penerbangan and nomor_tiket:
        if Klaim.objects.filter(
            email_member=member,
            flight_number=flight_number,
            tanggal_penerbangan=tanggal_penerbangan,
            nomor_tiket=nomor_tiket
        ).exists():
            errors.append('Klaim duplikat: penerbangan dengan data yang sama sudah pernah diajukan.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('klaim:member_list')

    Klaim.objects.create(
        email_member=member,
        maskapai_id=maskapai,
        bandara_asal_id=bandara_asal,
        bandara_tujuan_id=bandara_tujuan,
        tanggal_penerbangan=tanggal_penerbangan,
        flight_number=flight_number,
        kelas_kabin=kelas_kabin,
        nomor_tiket=nomor_tiket,
        pnr=pnr,
        status_penerimaan='Menunggu',
        timestamp=timezone.now(),
    )
    messages.success(request, 'Klaim berhasil diajukan dan sedang menunggu verifikasi.')
    return redirect('klaim:member_list')


@require_http_methods(['POST'])
def member_klaim_update(request, no_klaim):
    """Member mengubah klaim yang berstatus Menunggu"""
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

    klaim = get_object_or_404(Klaim, pk=no_klaim)
    if klaim.email_member_id != member.email_id:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')
    if klaim.status_penerimaan != 'Menunggu':
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

    if maskapai and not Maskapai.objects.filter(kode_maskapai=maskapai).exists():
        messages.error(request, 'Maskapai tidak valid.')
        return redirect('klaim:member_list')
    if bandara_asal and not Bandara.objects.filter(iata_code=bandara_asal).exists():
        messages.error(request, 'Bandara asal tidak valid.')
        return redirect('klaim:member_list')
    if bandara_tujuan and not Bandara.objects.filter(iata_code=bandara_tujuan).exists():
        messages.error(request, 'Bandara tujuan tidak valid.')
        return redirect('klaim:member_list')

    klaim.maskapai_id = maskapai
    klaim.bandara_asal_id = bandara_asal
    klaim.bandara_tujuan_id = bandara_tujuan
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
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')

    klaim = get_object_or_404(Klaim, pk=no_klaim)
    if klaim.email_member_id != member.email_id:
        messages.error(request, 'Akses ditolak.')
        return redirect('klaim:member_list')
    if klaim.status_penerimaan != 'Menunggu':
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
    if not _get_current_staf(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    filter_status   = request.GET.get('status', '')
    filter_maskapai = request.GET.get('maskapai', '')
    filter_tanggal  = request.GET.get('tanggal', '')

    qs = Klaim.objects.all().order_by('-timestamp')

    if filter_status:
        qs = qs.filter(status_penerimaan=filter_status)
    if filter_maskapai:
        qs = qs.filter(maskapai_id=filter_maskapai)
    if filter_tanggal:
        qs = qs.filter(timestamp__date=filter_tanggal)

    ctx = _context_base()
    ctx.update({
        'klaim_list':      [_to_klaim_view(k) for k in qs],
        'filter_status':   filter_status,
        'filter_maskapai': filter_maskapai,
        'filter_tanggal':  filter_tanggal,
    })
    return render(request, 'klaim/staf_list.html', ctx)


@require_http_methods(['POST'])
def staf_klaim_action(request, no_klaim):
    """Staf menyetujui atau menolak klaim"""
    if not _get_current_staf(request):
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    klaim = get_object_or_404(Klaim, pk=no_klaim)
    action = request.POST.get('action') # 'setujui' atau 'tolak'

    if klaim.status_penerimaan != 'Menunggu':
        messages.error(request, f'Klaim {no_klaim} sudah diproses sebelumnya.')
        return redirect('klaim:staf_list')

    staf = _get_current_staf(request)

    if action == 'setujui':
        klaim.status_penerimaan = 'Disetujui'
        if staf:
            klaim.email_staf = staf
        # Bersihkan notices lama
        if hasattr(connection.connection, 'notices'):
            del connection.connection.notices[:]

        klaim.save()

        # Tampilkan pesan dari Trigger (jika ada)
        if hasattr(connection.connection, 'notices') and connection.connection.notices:
            for notice in connection.connection.notices:
                clean_notice = notice.replace('NOTICE:  ', '').strip()
                messages.success(request, clean_notice)
        else:
            messages.success(request, f'Klaim {no_klaim} berhasil disetujui.')
    elif action == 'tolak':
        klaim.status_penerimaan = 'Ditolak'
        if staf:
            klaim.email_staf = staf
        klaim.save()
        messages.error(request, f'Klaim {no_klaim} telah ditolak.')
        
    return redirect('klaim:staf_list')
