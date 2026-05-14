from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import connection

# ── helper ───────────────────────────────────────────────────────────────────
def dictfetchall(cursor):
    """
    Fungsi bantuan untuk mengubah hasil cursor (tuple) menjadi list of dictionaries.
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


# ── R: list mitra ─────────────────────────────────────────────────────────────
@staf_required
def mitra_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.*, p.id as p_id, 
                   (SELECT COUNT(*) FROM aeromiles.hadiah h WHERE h.id_penyedia = m.id_penyedia) as hadiah_count
            FROM aeromiles.mitra m
            LEFT JOIN aeromiles.penyedia p ON m.id_penyedia = p.id
            ORDER BY m.nama_mitra ASC;
        """)
        mitra_list_qs = dictfetchall(cursor)
        
    return render(request, 'mitra/list.html', {'mitra_list': mitra_list_qs})


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
            
        with connection.cursor() as cursor:
            if email_mitra:
                cursor.execute("SELECT 1 FROM aeromiles.mitra WHERE email_mitra = %s;", [email_mitra])
                if cursor.fetchone():
                    errors.append('Email mitra sudah terdaftar dalam sistem.')

            if errors:
                for e in errors:
                    messages.error(request, e)
                return redirect('mitra:mitra_list')

            # Insert ke PENYEDIA lalu RETURNING id
            cursor.execute("INSERT INTO aeromiles.penyedia DEFAULT VALUES RETURNING id;")
            penyedia_id = cursor.fetchone()[0]
            
            # Insert ke MITRA
            cursor.execute("""
                INSERT INTO aeromiles.mitra (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama)
                VALUES (%s, %s, %s, %s);
            """, [email_mitra, penyedia_id, nama_mitra, tanggal_kerja_sama])

        messages.success(
            request,
            f'Mitra "{nama_mitra}" berhasil didaftarkan (ID Penyedia: #{penyedia_id}).'
        )
        return redirect('mitra:mitra_list')

    return render(request, 'mitra/form.html', {'mode': 'create'})


# ── U: edit mitra (email & id_penyedia tidak bisa diubah) ────────────────────
@staf_required
@require_http_methods(['GET', 'POST'])
def mitra_update(request, email_mitra):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM aeromiles.mitra WHERE email_mitra = %s;", [email_mitra])
        row = cursor.fetchone()
        if not row:
            messages.error(request, 'Mitra tidak ditemukan.')
            return redirect('mitra:mitra_list')
        
        columns = [col[0] for col in cursor.description]
        mitra = dict(zip(columns, row))

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

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE aeromiles.mitra 
                SET nama_mitra = %s, tanggal_kerja_sama = %s 
                WHERE email_mitra = %s;
            """, [nama_mitra, tanggal_kerja_sama, email_mitra])

        messages.success(request, f'Mitra "{nama_mitra}" berhasil diperbarui.')
        return redirect('mitra:mitra_list')

    return render(request, 'mitra/form.html', {
        'mitra': mitra,
        'mode': 'update',
    })


# ── D: hapus mitra (cascade ke Penyedia → Hadiah) ────────────────────────────
@staf_required
@require_http_methods(['POST'])
def mitra_delete(request, email_mitra):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_penyedia, nama_mitra FROM aeromiles.mitra WHERE email_mitra = %s;", [email_mitra])
        row = cursor.fetchone()
        if not row:
            messages.error(request, 'Mitra tidak ditemukan.')
            return redirect('mitra:mitra_list')
            
        id_penyedia = row[0]
        nama_mitra = row[1]

        # Menghapus penyedia akan cascade ke mitra dan hadiah di PostgreSQL 
        # (jika ada ON DELETE CASCADE. Jika tidak, delete hadiah dulu, lalu mitra, lalu penyedia).
        # Di schema django on_delete=models.CASCADE ada, tapi di raw SQL: 
        # REFERENCES PENYEDIA(id) (tanpa ON DELETE CASCADE).
        # Mari kita hapus manual untuk aman.
        
        # 1. Hapus Hadiah terkait penyedia ini
        cursor.execute("DELETE FROM aeromiles.hadiah WHERE id_penyedia = %s;", [id_penyedia])
        
        # 2. Hapus Mitra
        cursor.execute("DELETE FROM aeromiles.mitra WHERE email_mitra = %s;", [email_mitra])
        
        # 3. Hapus Penyedia
        cursor.execute("DELETE FROM aeromiles.penyedia WHERE id = %s;", [id_penyedia])

    messages.success(request, f'Mitra "{nama_mitra}" beserta hadiah terkait berhasil dihapus.')
    return redirect('mitra:mitra_list')