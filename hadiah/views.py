from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection

# ── helper ──────────────────────────────────────────────────────────────────
def dictfetchall(cursor):
    """
    Fungsi bantuan untuk mengubah hasil cursor menjadi list of dictionaries.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def staf_required(view_func):
    def wrapper(request, *args, **kwargs):
        # if not request.user.is_authenticated:
        #     return redirect('main:login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def generate_kode_hadiah():
    with connection.cursor() as cursor:
        cursor.execute("SELECT kode_hadiah FROM aeromiles.hadiah ORDER BY kode_hadiah DESC LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            return 'RWD-001'
        last_kode = row[0]
        try:
            num = int(last_kode.split('-')[1]) + 1
        except (IndexError, ValueError):
            cursor.execute("SELECT COUNT(*) FROM aeromiles.hadiah;")
            count = cursor.fetchone()[0]
            num = count + 1
        return f'RWD-{num:03d}'


# ── R: list hadiah ───────────────────────────────────────────────────────────
@staf_required
def hadiah_list(request):
    today = timezone.now().date()
    
    filter_penyedia = request.GET.get('penyedia', '')
    filter_status   = request.GET.get('status', '')

    with connection.cursor() as cursor:
        # Get penyedia list for dropdown
        cursor.execute("""
            SELECT p.id, m.nama_mitra 
            FROM aeromiles.penyedia p
            LEFT JOIN aeromiles.mitra m ON p.id = m.id_penyedia
            ORDER BY m.nama_mitra;
        """)
        penyedia_list = dictfetchall(cursor)

        # Base query for hadiah
        query = """
            SELECT h.*, m.nama_mitra 
            FROM aeromiles.hadiah h
            LEFT JOIN aeromiles.mitra m ON h.id_penyedia = m.id_penyedia
            WHERE 1=1
        """
        params = []

        if filter_penyedia:
            query += " AND h.id_penyedia = %s"
            params.append(filter_penyedia)
            
        if filter_status == 'aktif':
            query += " AND h.valid_start_date <= %s AND h.program_end >= %s"
            params.extend([today, today])
        elif filter_status == 'expired':
            query += " AND h.program_end < %s"
            params.append(today)

        query += " ORDER BY h.kode_hadiah ASC"
        
        cursor.execute(query, params)
        hadiah_list_qs = dictfetchall(cursor)

    return render(request, 'hadiah/list.html', {
        'hadiah_list': hadiah_list_qs,
        'penyedia_list': penyedia_list,
        'filter_penyedia': filter_penyedia,
        'filter_status': filter_status,
        'today': today,
    })


# ── C: tambah hadiah ─────────────────────────────────────────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def hadiah_create(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id, m.nama_mitra 
            FROM aeromiles.penyedia p
            LEFT JOIN aeromiles.mitra m ON p.id = m.id_penyedia
            ORDER BY m.nama_mitra;
        """)
        penyedia_list = dictfetchall(cursor)

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
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO aeromiles.hadiah (kode_hadiah, nama, id_penyedia, miles, deskripsi, valid_start_date, program_end)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, [kode, nama, id_penyedia_val, int(miles), deskripsi, valid_start_date, program_end])
            
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
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.*, m.nama_mitra 
            FROM aeromiles.hadiah h
            LEFT JOIN aeromiles.mitra m ON h.id_penyedia = m.id_penyedia
            WHERE h.kode_hadiah = %s;
        """, [kode_hadiah])
        hadiah_rows = dictfetchall(cursor)
        if not hadiah_rows:
            messages.error(request, 'Hadiah tidak ditemukan.')
            return redirect('hadiah:hadiah_list')
        hadiah = hadiah_rows[0]
        
        # We must make valid_start_date and program_end act like proper dates/strings for the template if needed
        # Postgres driver usually converts them to datetime.date
        
        cursor.execute("""
            SELECT p.id, m.nama_mitra 
            FROM aeromiles.penyedia p
            LEFT JOIN aeromiles.mitra m ON p.id = m.id_penyedia
            ORDER BY m.nama_mitra;
        """)
        penyedia_list = dictfetchall(cursor)

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

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE aeromiles.hadiah 
                SET nama = %s, id_penyedia = %s, miles = %s, deskripsi = %s, valid_start_date = %s, program_end = %s
                WHERE kode_hadiah = %s;
            """, [nama, id_penyedia_val, int(miles), deskripsi, valid_start_date, program_end, kode_hadiah])

        messages.success(request, f'Hadiah "{nama}" berhasil diperbarui.')
        return redirect('hadiah:hadiah_list')

    return render(request, 'hadiah/form.html', {
        'hadiah': hadiah,
        'penyedia_list': penyedia_list,
        'mode': 'update',
    })


@staf_required
@require_http_methods(['POST'])
def hadiah_delete(request, kode_hadiah):
    today = timezone.now().date()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM aeromiles.hadiah WHERE kode_hadiah = %s;", [kode_hadiah])
        row = cursor.fetchone()
        if not row:
            messages.error(request, 'Hadiah tidak ditemukan.')
            return redirect('hadiah:hadiah_list')
            
        columns = [col[0] for col in cursor.description]
        hadiah = dict(zip(columns, row))
        
        if hadiah['program_end'] >= today:
            messages.error(request, f'Hadiah "{hadiah["nama"]}" tidak dapat dihapus karena belum berakhir.')
            return redirect('hadiah:hadiah_list')

        cursor.execute("DELETE FROM aeromiles.hadiah WHERE kode_hadiah = %s;", [kode_hadiah])
        
    messages.success(request, f'Hadiah "{hadiah["nama"]}" berhasil dihapus.')
    return redirect('hadiah:hadiah_list')