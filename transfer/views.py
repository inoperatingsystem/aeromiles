from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Transfer

# Dummy login data
CURRENT_MEMBER_EMAIL = "john@example.com"
CURRENT_MEMBER_NAME = "John Doe"
AWARD_MILES_TERSEDIA = 32000

def transfer_list(request):
    """Member melihat riwayat transfer miles"""
    # Cari transfer di mana user ini pengirim ATAU penerima
    qs = Transfer.objects.all() # Dummy mode
    
    # Bikin list data untuk template karena ada logic Tipe (Kirim/Terima)
    transfers_data = []
    for t in qs:
        # Asumsi untuk dummy mode:
        # Jika pengirim_email == john@example.com, tipe = Kirim
        # Jika bukan, tipe = Terima
        if t.pengirim_email == CURRENT_MEMBER_EMAIL:
            tipe = 'Kirim'
            member_nama = t.penerima_nama
            member_email = t.penerima_email
            jumlah_tampil = f"-{t.jumlah_miles}"
        else:
            tipe = 'Terima'
            member_nama = t.pengirim_nama
            member_email = t.pengirim_email
            jumlah_tampil = f"+{t.jumlah_miles}"
            
        transfers_data.append({
            'waktu': t.waktu_transfer.strftime('%Y-%m-%d %H:%M'),
            'nama': member_nama,
            'email': member_email,
            'jumlah': jumlah_tampil,
            'catatan': t.catatan or '-',
            'tipe': tipe
        })
    
    ctx = {
        'transfers': transfers_data,
        'award_miles': f"{AWARD_MILES_TERSEDIA:,}",
        'role': 'member'
    }
    return render(request, 'transfer/list.html', ctx)

@require_http_methods(['POST'])
def transfer_create(request):
    """Member melakukan transfer miles"""
    penerima_email = request.POST.get('penerima_email', '').strip()
    jumlah_miles_str = request.POST.get('jumlah_miles', '').strip()
    catatan = request.POST.get('catatan', '').strip()
    
    errors = []
    
    if not penerima_email:
        errors.append("Email penerima wajib diisi.")
    elif penerima_email == CURRENT_MEMBER_EMAIL:
        errors.append("Anda tidak dapat mentransfer miles ke diri sendiri.")
        
    if not jumlah_miles_str:
        errors.append("Jumlah miles wajib diisi.")
    else:
        try:
            jumlah_miles = int(jumlah_miles_str)
            if jumlah_miles <= 0:
                errors.append("Jumlah miles harus lebih dari 0.")
            elif jumlah_miles > AWARD_MILES_TERSEDIA:
                errors.append("Award miles tidak mencukupi.")
        except ValueError:
            errors.append("Jumlah miles tidak valid.")
            
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('transfer:transfer_list')
        
    # Asumsikan email valid dan ada di sistem dummy
    # Create transfer record
    Transfer.objects.create(
        pengirim_email=CURRENT_MEMBER_EMAIL,
        pengirim_nama=CURRENT_MEMBER_NAME,
        penerima_email=penerima_email,
        penerima_nama=penerima_email.split('@')[0].capitalize(), # Dummy name
        jumlah_miles=jumlah_miles,
        catatan=catatan
    )
    
    messages.success(request, f"Berhasil mentransfer {jumlah_miles} miles ke {penerima_email}.")
    return redirect('transfer:transfer_list')
