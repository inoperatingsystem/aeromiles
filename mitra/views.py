from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from hadiah.models import Penyedia
from .models import Mitra


# ── helper ───────────────────────────────────────────────────────────────────
def staf_required(view_func):
    """
    Decorator: hanya staf yang boleh akses.
    TODO: aktifkan pengecekan autentikasi setelah modul auth selesai dibangun.
    Saat ini di-bypass untuk mode dummy/development.
    """
    def wrapper(request, *args, **kwargs):
        # Auth bypass — dummy mode, aktifkan kembali setelah auth selesai
        # if not request.user.is_authenticated:
        #     return redirect('main:login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ── R: list mitra ─────────────────────────────────────────────────────────────
@staf_required
def mitra_list(request):
    qs = Mitra.objects.select_related('id_penyedia').order_by('nama_mitra')
    return render(request, 'mitra/list.html', {'mitra_list': qs})


# ── C: tambah mitra (otomatis buat Penyedia baru) ────────────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def mitra_create(request):
    if request.method == 'POST':
        email_mitra        = request.POST.get('email_mitra', '').strip()
        nama_mitra         = request.POST.get('nama_mitra', '').strip()
        tanggal_kerja_sama = request.POST.get('tanggal_kerja_sama', '').strip()

        errors = []
        if not email_mitra:
            errors.append('Email mitra wajib diisi.')
        if not nama_mitra:
            errors.append('Nama mitra wajib diisi.')
        if not tanggal_kerja_sama:
            errors.append('Tanggal kerja sama wajib diisi.')
        if email_mitra and Mitra.objects.filter(email_mitra=email_mitra).exists():
            errors.append('Email mitra sudah terdaftar dalam sistem.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('mitra:mitra_list')

        # Buat Penyedia baru otomatis lalu asosiasikan ke Mitra
        penyedia_baru = Penyedia.objects.create()
        Mitra.objects.create(
            email_mitra=email_mitra,
            id_penyedia=penyedia_baru,
            nama_mitra=nama_mitra,
            tanggal_kerja_sama=tanggal_kerja_sama,
        )
        messages.success(
            request,
            f'Mitra "{nama_mitra}" berhasil didaftarkan (ID Penyedia: #{penyedia_baru.id}).'
        )
        return redirect('mitra:mitra_list')

    return render(request, 'mitra/form.html', {'mode': 'create'})


# ── U: edit mitra (email & id_penyedia tidak bisa diubah) ────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def mitra_update(request, email_mitra):
    mitra = get_object_or_404(Mitra, email_mitra=email_mitra)

    if request.method == 'POST':
        nama_mitra         = request.POST.get('nama_mitra', '').strip()
        tanggal_kerja_sama = request.POST.get('tanggal_kerja_sama', '').strip()

        errors = []
        if not nama_mitra:
            errors.append('Nama mitra wajib diisi.')
        if not tanggal_kerja_sama:
            errors.append('Tanggal kerja sama wajib diisi.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('mitra:mitra_list')

        mitra.nama_mitra         = nama_mitra
        mitra.tanggal_kerja_sama = tanggal_kerja_sama
        mitra.save()

        messages.success(request, f'Mitra "{mitra.nama_mitra}" berhasil diperbarui.')
        return redirect('mitra:mitra_list')

    return render(request, 'mitra/form.html', {
        'mitra': mitra,
        'mode': 'update',
    })


# ── D: hapus mitra (cascade ke Penyedia → Hadiah) ────────────────────────────
@staf_required
@require_http_methods(['POST'])
def mitra_delete(request, email_mitra):
    mitra = get_object_or_404(Mitra, email_mitra=email_mitra)
    nama  = mitra.nama_mitra

    # Hapus Penyedia → cascade ke Mitra & seluruh Hadiah milik penyedia ini
    mitra.id_penyedia.delete()

    messages.success(request, f'Mitra "{nama}" beserta hadiah terkait berhasil dihapus.')
    return redirect('mitra:mitra_list')