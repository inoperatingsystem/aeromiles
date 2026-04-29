from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect

# FITUR 2: Login
def login_view(request):
    # Untuk dummy UI, kita beri opsi simulasi di template nanti
    return render(request, 'login.html')

# FITUR 2: Logout
def logout_view(request):
    # Simulasi logout kembali ke halaman login
    return redirect('main:login')

# FITUR 3: Registrasi
def register_view(request):
    return render(request, 'register.html')

# FITUR 4: Dashboard
def dashboard_view(request):
    # Simulasi role menggunakan parameter URL (?role=staf atau ?role=member)
    role = request.GET.get('role', 'member') 
    
    context = {
        'role': role,
        'nama_lengkap': 'Mr. John William Doe' if role == 'member' else 'Mr. Admin Aero',
        'email': 'john@example.com' if role == 'member' else 'admin@aeromiles.com',
        'kewarganegaraan': 'Indonesia',
        'tanggal_lahir': '1990-05-15' if role == 'member' else '1988-01-01',
        'telepon': '+62 81234567890' if role == 'member' else '+62 81111111111',
    }

    if role == 'member':
        context.update({
            'nomor_member': 'M0001',
            'tier': 'Gold',
            'total_miles': '45,000',
            'award_miles': '32,000',
            'tanggal_bergabung': '2024-01-15',
        })
    else:
        context.update({
            'id_staf': 'S0001',
            'maskapai': 'Garuda Indonesia',
            'klaim_menunggu': '2',
            'klaim_disetujui': '1/1',
        })

    return render(request, 'dashboard.html', context)

# FITUR 5: Pengaturan Profil
def profile_view(request):
    role = request.GET.get('role', 'member')
    context = {
        'role': role,
        'email': 'john@example.com' if role == 'member' else 'admin@aeromiles.com',
        'salutation': 'Mr.',
        'nama_depan': 'John' if role == 'member' else 'Admin',
        'nama_tengah': 'William' if role == 'member' else '',
        'nama_belakang': 'Doe' if role == 'member' else 'Aero',
        'country_code': '+62',
        'nomor_hp': '81234567890' if role == 'member' else '81111111111',
        'kewarganegaraan': 'Indonesia',
        'tanggal_lahir': '1990-05-15' if role == 'member' else '1988-01-01',
    }

    if role == 'member':
        context.update({
            'nomor_member': 'M0001',
            'tanggal_bergabung': '2024-01-15'
        })
    else:
        context.update({
            'id_staf': 'S0001',
            'maskapai': 'GA - Garuda Indonesia'
        })
        
    return render(request, 'profile.html', context)

# FITUR 6: Manajemen Data Member (Khusus Staf)
def member_list_view(request):
    # Data dummy member untuk ditampilkan di tabel
    dummy_members = [
        {'no': 'M0001', 'nama': 'Mr. John William Doe', 'email': 'john@example.com', 'tier': 'Gold', 'total_miles': '45,000', 'award_miles': '32,000', 'bergabung': '2024-01-15'},
        {'no': 'M0002', 'nama': 'Mrs. Jane Smith', 'email': 'jane@example.com', 'tier': 'Silver', 'total_miles': '20,000', 'award_miles': '15,000', 'bergabung': '2024-03-10'},
        {'no': 'M0003', 'nama': 'Mr. Budi Anto Santoso', 'email': 'budi@example.com', 'tier': 'Blue', 'total_miles': '5,000', 'award_miles': '3,500', 'bergabung': '2024-06-20'},
    ]
    
    context = {
        'role': 'staf', # Hardcode role staf karena halaman ini khusus staf
        'members': dummy_members,
        'nama_lengkap': 'Mr. Admin Aero'
    }
    return render(request, 'member_list.html', context)

# FITUR 7: Manajemen Identitas (Khusus Member)
def identity_list_view(request):
    # Data dummy identitas untuk ditampilkan di tabel
    dummy_identities = [
        {'no': 'A12345678', 'jenis': 'Paspor', 'negara': 'Indonesia', 'terbit': '2020-01-15', 'habis': '2030-01-15', 'status': 'Aktif'},
        {'no': '3275012345678901', 'jenis': 'KTP', 'negara': 'Indonesia', 'terbit': '2010-06-01', 'habis': '2024-06-01', 'status': 'Kedaluwarsa'},
    ]
    
    context = {
        'role': 'member', # Hardcode role member karena halaman ini khusus member
        'identities': dummy_identities,
        'nama_lengkap': 'Mr. John William Doe'
    }
    return render(request, 'identity_list.html', context)