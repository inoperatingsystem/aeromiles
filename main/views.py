from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Identitas
from .forms import RegisterForm, ProfileForm, IdentitasForm
from django.db.models import Sum

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
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            user = User.objects.create_user(username=email, email=email, password=password)
            
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            
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
    profile = request.user.userprofile
    context = {
        'role': profile.role,
        'nama_lengkap': profile.full_name,
        'email': request.user.email,
        'kewarganegaraan': profile.nationality,
        'tanggal_lahir': profile.dob,
        'telepon': f"{profile.country_code} {profile.phone_number}",
    }

    if profile.role == 'member':
        # TODO: Calculate total miles and award miles from transactions if needed, for now use profile fields
        context.update({
            'nomor_member': profile.member_number,
            'tier': profile.tier,
            'total_miles': profile.total_miles,
            'award_miles': profile.award_miles,
            'tanggal_bergabung': profile.join_date,
        })
    else:
        # Dummy data for staf claims since claim is in another app
        context.update({
            'id_staf': profile.staf_id,
            'maskapai': profile.kode_maskapai,
            'klaim_menunggu': '2', # TODO: count from klaim model
            'klaim_disetujui': '1', # TODO: count from klaim model
            'klaim_ditolak': '1', # TODO: count from klaim model
        })

    return render(request, 'dashboard.html', context)

# FITUR: Pengaturan Profil & Ubah Password
@login_required(login_url='main:login')
def profile_view(request):
    profile = request.user.userprofile
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
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

    form = ProfileForm(instance=profile)
    context = {
        'role': profile.role,
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile.html', context)

# FITUR: Manajemen Data Member (Khusus Staf)
@login_required(login_url='main:login')
def member_list_view(request):
    if request.user.userprofile.role != 'staf':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        member_id = request.POST.get('member_id')
        
        if action == 'delete' and member_id:
            member_profile = get_object_or_404(UserProfile, id=member_id, role='member')
            member_profile.user.delete() # Automatically deletes profile due to CASCADE
            messages.success(request, 'Member berhasil dihapus.')
        elif action == 'edit' and member_id:
            member_profile = get_object_or_404(UserProfile, id=member_id, role='member')
            member_profile.salutation = request.POST.get('salutation')
            member_profile.first_mid_name = request.POST.get('first_mid_name')
            member_profile.last_name = request.POST.get('last_name')
            member_profile.country_code = request.POST.get('country_code')
            member_profile.phone_number = request.POST.get('phone_number')
            member_profile.nationality = request.POST.get('nationality')
            member_profile.dob = request.POST.get('dob')
            member_profile.tier = request.POST.get('tier')
            member_profile.save()
            messages.success(request, 'Data member berhasil diperbarui.')
        elif action == 'create':
            # Simplified creation
            email = request.POST.get('email')
            password = request.POST.get('password')
            if User.objects.filter(username=email).exists():
                messages.error(request, 'Email sudah terdaftar.')
            else:
                user = User.objects.create_user(username=email, email=email, password=password)
                UserProfile.objects.create(
                    user=user,
                    role='member',
                    salutation=request.POST.get('salutation'),
                    first_mid_name=request.POST.get('first_mid_name'),
                    last_name=request.POST.get('last_name'),
                    country_code=request.POST.get('country_code'),
                    phone_number=request.POST.get('phone_number'),
                    nationality=request.POST.get('nationality'),
                    dob=request.POST.get('dob'),
                )
                messages.success(request, 'Member baru berhasil ditambahkan.')
        return redirect('main:member_list')

    members = UserProfile.objects.filter(role='member').order_by('-join_date')
    context = {
        'role': 'staf',
        'members': members,
    }
    return render(request, 'member_list.html', context)

# FITUR: Manajemen Identitas (Khusus Member)
@login_required(login_url='main:login')
def identity_list_view(request):
    if request.user.userprofile.role != 'member':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        identity_id = request.POST.get('identity_id')
        
        if action == 'delete' and identity_id:
            identitas = get_object_or_404(Identitas, id=identity_id, user_profile=request.user.userprofile)
            identitas.delete()
            messages.success(request, 'Identitas berhasil dihapus.')
        elif action == 'edit' and identity_id:
            identitas = get_object_or_404(Identitas, id=identity_id, user_profile=request.user.userprofile)
            identitas.jenis = request.POST.get('jenis')
            identitas.negara_penerbit = request.POST.get('negara_penerbit')
            identitas.tanggal_terbit = request.POST.get('tanggal_terbit')
            identitas.tanggal_habis = request.POST.get('tanggal_habis')
            identitas.save()
            messages.success(request, 'Identitas berhasil diperbarui.')
        elif action == 'create':
            no_dok = request.POST.get('no_dokumen')
            if Identitas.objects.filter(no_dokumen=no_dok).exists():
                messages.error(request, 'Nomor dokumen sudah terdaftar di sistem.')
            else:
                Identitas.objects.create(
                    user_profile=request.user.userprofile,
                    no_dokumen=no_dok,
                    jenis=request.POST.get('jenis'),
                    negara_penerbit=request.POST.get('negara_penerbit'),
                    tanggal_terbit=request.POST.get('tanggal_terbit'),
                    tanggal_habis=request.POST.get('tanggal_habis')
                )
                messages.success(request, 'Identitas baru berhasil ditambahkan.')
        return redirect('main:identity_list')

    identities = request.user.userprofile.identitas.all()
    context = {
        'role': 'member',
        'identities': identities,
    }
    return render(request, 'identity_list.html', context)