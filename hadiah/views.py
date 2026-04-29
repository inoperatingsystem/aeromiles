from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Penyedia, Hadiah, generate_kode_hadiah


# ── helper ──────────────────────────────────────────────────────────────────
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


# ── R: list hadiah ───────────────────────────────────────────────────────────
@staf_required
def hadiah_list(request):
    today = timezone.now().date()
    qs = Hadiah.objects.select_related('id_penyedia').all()

    filter_penyedia = request.GET.get('penyedia', '')
    filter_status   = request.GET.get('status', '')

    if filter_penyedia:
        qs = qs.filter(id_penyedia__id=filter_penyedia)
    if filter_status == 'aktif':
        qs = qs.filter(valid_start_date__lte=today, program_end__gte=today)
    elif filter_status == 'expired':
        qs = qs.filter(program_end__lt=today)

    return render(request, 'hadiah/list.html', {
        'hadiah_list': qs,
        'penyedia_list': Penyedia.objects.all(),
        'filter_penyedia': filter_penyedia,
        'filter_status': filter_status,
        'today': today,
    })


# ── C: tambah hadiah ─────────────────────────────────────────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def hadiah_create(request):
    penyedia_list = Penyedia.objects.all()

    if request.method == 'POST':
        nama             = request.POST.get('nama', '').strip()
        id_penyedia_val  = request.POST.get('id_penyedia', '').strip()
        miles            = request.POST.get('miles', '').strip()
        deskripsi        = request.POST.get('deskripsi', '').strip()
        valid_start_date = request.POST.get('valid_start_date', '').strip()
        program_end      = request.POST.get('program_end', '').strip()

        errors = []
        if not nama:             errors.append('Nama hadiah wajib diisi.')
        if not id_penyedia_val:  errors.append('Penyedia wajib dipilih.')
        if not miles or not miles.isdigit() or int(miles) < 1:
            errors.append('Miles harus berupa angka positif.')
        if not valid_start_date: errors.append('Valid start date wajib diisi.')
        if not program_end:      errors.append('Program end wajib diisi.')
        if valid_start_date and program_end and valid_start_date > program_end:
            errors.append('Valid start date tidak boleh setelah program end.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('hadiah:hadiah_list')

        kode = generate_kode_hadiah()
        Hadiah.objects.create(
            kode_hadiah=kode,
            nama=nama,
            id_penyedia=get_object_or_404(Penyedia, id=id_penyedia_val),
            miles=int(miles),
            deskripsi=deskripsi,
            valid_start_date=valid_start_date,
            program_end=program_end,
        )
        messages.success(request, f'Hadiah "{nama}" berhasil ditambahkan dengan kode {kode}.')
        return redirect('hadiah:hadiah_list')

    return render(request, 'hadiah/form.html', {
        'penyedia_list': penyedia_list,
        'mode': 'create',
    })


# ── U: edit hadiah ───────────────────────────────────────────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def hadiah_update(request, kode_hadiah):
    hadiah        = get_object_or_404(Hadiah, kode_hadiah=kode_hadiah)
    penyedia_list = Penyedia.objects.all()

    if request.method == 'POST':
        nama             = request.POST.get('nama', '').strip()
        id_penyedia_val  = request.POST.get('id_penyedia', '').strip()
        miles            = request.POST.get('miles', '').strip()
        deskripsi        = request.POST.get('deskripsi', '').strip()
        valid_start_date = request.POST.get('valid_start_date', '').strip()
        program_end      = request.POST.get('program_end', '').strip()

        errors = []
        if not nama:             errors.append('Nama hadiah wajib diisi.')
        if not id_penyedia_val:  errors.append('Penyedia wajib dipilih.')
        if not miles or not miles.isdigit() or int(miles) < 1:
            errors.append('Miles harus berupa angka positif.')
        if not valid_start_date: errors.append('Valid start date wajib diisi.')
        if not program_end:      errors.append('Program end wajib diisi.')
        if valid_start_date and program_end and valid_start_date > program_end:
            errors.append('Valid start date tidak boleh setelah program end.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('hadiah:hadiah_list')

        hadiah.nama             = nama
        hadiah.id_penyedia      = get_object_or_404(Penyedia, id=id_penyedia_val)
        hadiah.miles            = int(miles)
        hadiah.deskripsi        = deskripsi
        hadiah.valid_start_date = valid_start_date
        hadiah.program_end      = program_end
        hadiah.save()

        messages.success(request, f'Hadiah "{hadiah.nama}" berhasil diperbarui.')
        return redirect('hadiah:hadiah_list')

    return render(request, 'hadiah/form.html', {
        'hadiah': hadiah,
        'penyedia_list': penyedia_list,
        'mode': 'update',
    })


@staf_required
@require_http_methods(['POST'])
def hadiah_delete(request, kode_hadiah):
    hadiah = get_object_or_404(Hadiah, kode_hadiah=kode_hadiah)

    if not hadiah.is_expired():
        messages.error(request, f'Hadiah "{hadiah.nama}" tidak dapat dihapus karena belum berakhir.')
        return redirect('hadiah:hadiah_list')

    nama = hadiah.nama
    hadiah.delete()
    messages.success(request, f'Hadiah "{nama}" berhasil dihapus.')
    return redirect('hadiah:hadiah_list')