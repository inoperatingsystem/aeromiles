import random
from types import SimpleNamespace

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Pengguna, Member, Staf, Identitas, Tier, Maskapai
from .forms import RegisterForm, ProfileForm


def _get_pengguna(request):
    if not request.user.is_authenticated:
        return None
    return Pengguna.objects.filter(email=request.user.email).first()


def _get_member(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        return None
    return Member.objects.filter(email=pengguna).select_related('email', 'id_tier').first()


def _get_staf(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        return None
    return Staf.objects.filter(email=pengguna).select_related('email', 'kode_maskapai').first()


def _generate_member_number():
    for _ in range(5):
        value = f"M{random.randint(100000, 999999)}"
        if not Member.objects.filter(nomor_member=value).exists():
            return value
    return f"M{Member.objects.count() + 1:06d}"


def _generate_staf_id():
    for _ in range(5):
        value = f"S{random.randint(100000, 999999)}"
        if not Staf.objects.filter(id_staf=value).exists():
            return value
    return f"S{Staf.objects.count() + 1:06d}"

# FITUR: Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('main:dashboard')
        else:
            messages.error(request, 'Email atau password salah.')
    return render(request, 'login.html')

# FITUR: Logout
def logout_view(request):
    logout(request)
    return redirect('main:login')

# FITUR: Registrasi
def register_view(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            role = data.get('role')
            email = data.get('email')
            password = data.get('password')

            tier = None
            if role == 'member':
                tier = Tier.objects.order_by('id_tier').first()
                if not tier:
                    messages.error(request, 'Tier belum tersedia. Hubungi admin untuk menambahkan data tier.')
                    return redirect('main:register')

            maskapai = None
            if role == 'staf':
                maskapai = Maskapai.objects.filter(kode_maskapai=data.get('kode_maskapai')).first()
                if not maskapai:
                    messages.error(request, 'Kode maskapai tidak valid.')
                    return redirect('main:register')

            if User.objects.filter(username=email).exists() or Pengguna.objects.filter(email=email).exists():
                messages.error(request, 'Email sudah terdaftar.')
                return redirect('main:register')

            user = User.objects.create_user(username=email, email=email, password=password)
            pengguna = Pengguna.objects.create(
                email=email,
                password=user.password,
                salutation=data.get('salutation'),
                first_mid_name=data.get('first_mid_name'),
                last_name=data.get('last_name'),
                country_code=data.get('country_code'),
                mobile_number=data.get('phone_number'),
                tanggal_lahir=data.get('dob'),
                kewarganegaraan=data.get('nationality'),
            )

            if role == 'member':
                Member.objects.create(
                    email=pengguna,
                    nomor_member=_generate_member_number(),
                    tanggal_bergabung=timezone.now().date(),
                    id_tier=tier,
                    award_miles=0,
                    total_miles=0,
                )
            else:
                Staf.objects.create(
                    email=pengguna,
                    id_staf=_generate_staf_id(),
                    kode_maskapai=maskapai,
                )

            messages.success(request, 'Registrasi berhasil. Silakan login.')
            return redirect('main:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
        
    return render(request, 'register.html', {'form': form})

# FITUR: Dashboard
@login_required(login_url='main:login')
def dashboard_view(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        messages.error(request, 'Data pengguna tidak ditemukan. Silakan login ulang.')
        return redirect('main:login')

    member = Member.objects.filter(email=pengguna).select_related('id_tier').first()
    staf = Staf.objects.filter(email=pengguna).select_related('kode_maskapai').first()

    role = 'member' if member else 'staf' if staf else 'guest'
    context = {
        'role': role,
        'nama_lengkap': pengguna.full_name,
        'email': pengguna.email,
        'kewarganegaraan': pengguna.kewarganegaraan,
        'tanggal_lahir': pengguna.tanggal_lahir,
        'telepon': f"{pengguna.country_code} {pengguna.mobile_number}",
    }

    if role == 'member' and member:
        context.update({
            'nomor_member': member.nomor_member,
            'tier': member.id_tier.nama if member.id_tier_id else member.id_tier_id,
            'total_miles': member.total_miles or 0,
            'award_miles': member.award_miles or 0,
            'tanggal_bergabung': member.tanggal_bergabung,
        })
    elif role == 'staf' and staf:
        context.update({
            'id_staf': staf.id_staf,
            'maskapai': staf.kode_maskapai_id,
            'klaim_menunggu': '2',
            'klaim_disetujui': '1',
            'klaim_ditolak': '1',
        })

    return render(request, 'dashboard.html', context)

# FITUR: Pengaturan Profil & Ubah Password
@login_required(login_url='main:login')
def profile_view(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('main:login')

    member = Member.objects.filter(email=pengguna).first()
    staf = Staf.objects.filter(email=pengguna).first()
    role = 'member' if member else 'staf' if staf else 'guest'

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = ProfileForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pengguna.salutation = data.get('salutation')
                pengguna.first_mid_name = data.get('first_mid_name')
                pengguna.last_name = data.get('last_name')
                pengguna.country_code = data.get('country_code')
                pengguna.mobile_number = data.get('phone_number')
                pengguna.tanggal_lahir = data.get('dob')
                pengguna.kewarganegaraan = data.get('nationality')
                pengguna.save()

                if role == 'staf' and staf:
                    kode_maskapai = data.get('kode_maskapai')
                    if kode_maskapai:
                        maskapai = Maskapai.objects.filter(kode_maskapai=kode_maskapai).first()
                        if not maskapai:
                            messages.error(request, 'Kode maskapai tidak valid.')
                            return redirect('main:profile')
                        staf.kode_maskapai = maskapai
                        staf.save()

                messages.success(request, 'Profil berhasil diperbarui.')
                return redirect('main:profile')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                        
        elif 'change_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(old_password):
                messages.error(request, 'Password lama salah.')
            elif new_password != confirm_password:
                messages.error(request, 'Konfirmasi password baru tidak cocok.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user) # Keep user logged in
                messages.success(request, 'Password berhasil diubah.')
                return redirect('main:profile')

    form = ProfileForm(initial={
        'salutation': pengguna.salutation,
        'first_mid_name': pengguna.first_mid_name,
        'last_name': pengguna.last_name,
        'country_code': pengguna.country_code,
        'phone_number': pengguna.mobile_number,
        'dob': pengguna.tanggal_lahir,
        'nationality': pengguna.kewarganegaraan,
        'kode_maskapai': staf.kode_maskapai_id if staf else '',
    })

    profile = SimpleNamespace(
        salutation=pengguna.salutation,
        first_mid_name=pengguna.first_mid_name,
        last_name=pengguna.last_name,
        country_code=pengguna.country_code,
        phone_number=pengguna.mobile_number,
        dob=pengguna.tanggal_lahir,
        nationality=pengguna.kewarganegaraan,
    )
    if member:
        profile.member_number = member.nomor_member
        profile.join_date = member.tanggal_bergabung
    if staf:
        profile.staf_id = staf.id_staf
        profile.kode_maskapai = staf.kode_maskapai_id

    context = {
        'role': role,
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile.html', context)

# FITUR: Manajemen Data Member (Khusus Staf)
@login_required(login_url='main:login')
def member_list_view(request):
    staf = _get_staf(request)
    if not staf:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        member_id = request.POST.get('member_id')
        
        if action == 'delete' and member_id:
            member = get_object_or_404(Member, nomor_member=member_id)
            pengguna = member.email
            member.delete()
            Pengguna.objects.filter(email=pengguna.email).delete()
            User.objects.filter(username=pengguna.email).delete()
            messages.success(request, 'Member berhasil dihapus.')
        elif action == 'edit' and member_id:
            member = get_object_or_404(Member, nomor_member=member_id)
            pengguna = member.email
            pengguna.salutation = request.POST.get('salutation')
            pengguna.first_mid_name = request.POST.get('first_mid_name')
            pengguna.last_name = request.POST.get('last_name')
            pengguna.country_code = request.POST.get('country_code')
            pengguna.mobile_number = request.POST.get('phone_number')
            pengguna.kewarganegaraan = request.POST.get('nationality')
            pengguna.tanggal_lahir = request.POST.get('dob')

            tier_value = request.POST.get('tier')
            tier = Tier.objects.filter(nama=tier_value).first() or Tier.objects.filter(id_tier=tier_value).first()
            if not tier:
                messages.error(request, 'Tier tidak valid.')
                return redirect('main:member_list')

            member.id_tier = tier
            pengguna.save()
            member.save()
            messages.success(request, 'Data member berhasil diperbarui.')
        elif action == 'create':
            email = request.POST.get('email')
            password = request.POST.get('password')
            if User.objects.filter(username=email).exists() or Pengguna.objects.filter(email=email).exists():
                messages.error(request, 'Email sudah terdaftar.')
                return redirect('main:member_list')

            tier = Tier.objects.order_by('id_tier').first()
            if not tier:
                messages.error(request, 'Tier belum tersedia. Hubungi admin.')
                return redirect('main:member_list')

            user = User.objects.create_user(username=email, email=email, password=password)
            pengguna = Pengguna.objects.create(
                email=email,
                password=user.password,
                salutation=request.POST.get('salutation'),
                first_mid_name=request.POST.get('first_mid_name'),
                last_name=request.POST.get('last_name'),
                country_code=request.POST.get('country_code'),
                mobile_number=request.POST.get('phone_number'),
                kewarganegaraan=request.POST.get('nationality'),
                tanggal_lahir=request.POST.get('dob'),
            )
            Member.objects.create(
                email=pengguna,
                nomor_member=_generate_member_number(),
                tanggal_bergabung=timezone.now().date(),
                id_tier=tier,
                award_miles=0,
                total_miles=0,
            )
            messages.success(request, 'Member baru berhasil ditambahkan.')
        return redirect('main:member_list')

    members_qs = Member.objects.select_related('email', 'id_tier').order_by('-tanggal_bergabung')
    members = []
    for member in members_qs:
        pengguna = member.email
        members.append(SimpleNamespace(
            id=member.nomor_member,
            member_number=member.nomor_member,
            full_name=pengguna.full_name,
            user=SimpleNamespace(email=pengguna.email),
            tier=member.id_tier.nama if member.id_tier_id else member.id_tier_id,
            total_miles=member.total_miles or 0,
            award_miles=member.award_miles or 0,
            join_date=member.tanggal_bergabung,
            salutation=pengguna.salutation,
            first_mid_name=pengguna.first_mid_name,
            last_name=pengguna.last_name,
            nationality=pengguna.kewarganegaraan,
            country_code=pengguna.country_code,
            phone_number=pengguna.mobile_number,
            dob=pengguna.tanggal_lahir,
        ))
    context = {
        'role': 'staf',
        'members': members,
    }
    return render(request, 'member_list.html', context)

# FITUR: Manajemen Identitas (Khusus Member)
@login_required(login_url='main:login')
def identity_list_view(request):
    member = _get_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        identity_id = request.POST.get('identity_id')
        
        if action == 'delete' and identity_id:
            identitas = get_object_or_404(Identitas, nomor=identity_id, email_member=member)
            identitas.delete()
            messages.success(request, 'Identitas berhasil dihapus.')
        elif action == 'edit' and identity_id:
            identitas = get_object_or_404(Identitas, nomor=identity_id, email_member=member)
            identitas.jenis = request.POST.get('jenis')
            identitas.negara_penerbit = request.POST.get('negara_penerbit')
            identitas.tanggal_terbit = request.POST.get('tanggal_terbit')
            identitas.tanggal_habis = request.POST.get('tanggal_habis')
            identitas.save()
            messages.success(request, 'Identitas berhasil diperbarui.')
        elif action == 'create':
            no_dok = request.POST.get('no_dokumen')
            if Identitas.objects.filter(nomor=no_dok).exists():
                messages.error(request, 'Nomor dokumen sudah terdaftar di sistem.')
            else:
                Identitas.objects.create(
                    email_member=member,
                    nomor=no_dok,
                    jenis=request.POST.get('jenis'),
                    negara_penerbit=request.POST.get('negara_penerbit'),
                    tanggal_terbit=request.POST.get('tanggal_terbit'),
                    tanggal_habis=request.POST.get('tanggal_habis'),
                )
                messages.success(request, 'Identitas baru berhasil ditambahkan.')
        return redirect('main:identity_list')

    identities_qs = Identitas.objects.filter(email_member=member)
    identities = [
        SimpleNamespace(
            id=ident.nomor,
            no_dokumen=ident.nomor,
            jenis=ident.jenis,
            negara_penerbit=ident.negara_penerbit,
            tanggal_terbit=ident.tanggal_terbit,
            tanggal_habis=ident.tanggal_habis,
        )
        for ident in identities_qs
    ]
    context = {
        'role': 'member',
        'identities': identities,
    }
    return render(request, 'identity_list.html', context)