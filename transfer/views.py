from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone

from main.models import Member
from .models import Transfer

def _get_current_member(request):
    if not request.user.is_authenticated:
        return None
    return Member.objects.filter(email_id=request.user.email).select_related('email').first()

def transfer_list(request):
    """Member melihat riwayat transfer miles"""
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    qs = Transfer.objects.filter(
        Q(email_member_1=member) | Q(email_member_2=member)
    ).select_related('email_member_1__email', 'email_member_2__email').order_by('-timestamp')
    
    # Bikin list data untuk template karena ada logic Tipe (Kirim/Terima)
    transfers_data = []
    for t in qs:
        # Asumsi untuk dummy mode:
        # Jika pengirim_email == john@example.com, tipe = Kirim
        # Jika bukan, tipe = Terima
        if t.email_member_1_id == member.email_id:
            tipe = 'Kirim'
            other_member = t.email_member_2
            member_nama = other_member.email.full_name if other_member and other_member.email else other_member.email_id
            member_email = other_member.email_id
            jumlah_tampil = f"-{t.jumlah}"
        else:
            tipe = 'Terima'
            other_member = t.email_member_1
            member_nama = other_member.email.full_name if other_member and other_member.email else other_member.email_id
            member_email = other_member.email_id
            jumlah_tampil = f"+{t.jumlah}"
            
        transfers_data.append({
            'waktu': t.timestamp.strftime('%Y-%m-%d %H:%M'),
            'nama': member_nama,
            'email': member_email,
            'jumlah': jumlah_tampil,
            'catatan': t.catatan or '-',
            'tipe': tipe
        })
    
    ctx = {
        'transfers': transfers_data,
        'award_miles': f"{(member.award_miles or 0):,}",
        'role': 'member'
    }
    return render(request, 'transfer/list.html', ctx)

@require_http_methods(['POST'])
def transfer_create(request):
    """Member melakukan transfer miles"""
    member = _get_current_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('transfer:transfer_list')

    penerima_email = request.POST.get('penerima_email', '').strip()
    jumlah_miles_str = request.POST.get('jumlah_miles', '').strip()
    catatan = request.POST.get('catatan', '').strip()
    
    errors = []
    
    if not penerima_email:
        errors.append("Email penerima wajib diisi.")
    elif penerima_email == member.email_id:
        errors.append("Anda tidak dapat mentransfer miles ke diri sendiri.")
        
    if not jumlah_miles_str:
        errors.append("Jumlah miles wajib diisi.")
    else:
        try:
            jumlah_miles = int(jumlah_miles_str)
            if jumlah_miles <= 0:
                errors.append("Jumlah miles harus lebih dari 0.")
            elif jumlah_miles > (member.award_miles or 0):
                errors.append("Award miles tidak mencukupi.")
        except ValueError:
            errors.append("Jumlah miles tidak valid.")
            
    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('transfer:transfer_list')
        
    penerima_member = Member.objects.filter(email_id=penerima_email).first()
    if not penerima_member:
        messages.error(request, 'Email penerima belum terdaftar sebagai member.')
        return redirect('transfer:transfer_list')

    Transfer.objects.create(
        email_member_1=member,
        email_member_2=penerima_member,
        timestamp=timezone.now(),
        jumlah=jumlah_miles,
        catatan=catatan or None,
    )
    
    messages.success(request, f"Berhasil mentransfer {jumlah_miles} miles ke {penerima_email}.")
    return redirect('transfer:transfer_list')
