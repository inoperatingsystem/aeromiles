import random
from types import SimpleNamespace

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.db import connection
from .models import Pengguna, Member, Staf
from .forms import RegisterForm, ProfileForm
from .utils import dictfetchall, dictfetchone


def _get_pengguna(request):
    if not request.user.is_authenticated:
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM pengguna WHERE email = %s", [request.user.email])
        row = dictfetchone(cursor)
        if row:
            return Pengguna(**row)
    return None


def _get_member(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        return None
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.*, t.nama as tier_nama 
            FROM member m 
            JOIN tier t ON m.id_tier = t.id_tier 
            WHERE m.email = %s
        """, [pengguna.email])
        row = dictfetchone(cursor)
        if row:
            data = {k: v for k, v in row.items() if k != 'tier_nama'}
            if 'email' in data: data['email_id'] = data.pop('email')
            if 'id_tier' in data: data['id_tier_id'] = data.pop('id_tier')
            
            member = Member(**data)
            member.tier_nama = row.get('tier_nama')
            return member
    return None


def _get_staf(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM staf WHERE email = %s", [pengguna.email])
        row = dictfetchone(cursor)
        if row:
            data = row.copy()
            if 'email' in data: data['email_id'] = data.pop('email')
            if 'kode_maskapai' in data: data['kode_maskapai_id'] = data.pop('kode_maskapai')
            return Staf(**data)
    return None


def _generate_member_number():
    with connection.cursor() as cursor:
        for _ in range(5):
            value = f"M{random.randint(100000, 999999)}"
            cursor.execute("SELECT 1 FROM member WHERE nomor_member = %s", [value])
            if not cursor.fetchone():
                return value
        
        cursor.execute("SELECT COUNT(*) FROM member")
        count = cursor.fetchone()[0]
        return f"M{count + 1:06d}"


def _generate_staf_id():
    with connection.cursor() as cursor:
        for _ in range(5):
            value = f"S{random.randint(100000, 999999)}"
            cursor.execute("SELECT 1 FROM staf WHERE id_staf = %s", [value])
            if not cursor.fetchone():
                return value
        
        cursor.execute("SELECT COUNT(*) FROM staf")
        count = cursor.fetchone()[0]
        return f"S{count + 1:06d}"

def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            domain = email.split('@')[-1]
            allowed_staff_domains = [
                'nusantaraair.com',
                'lionsky.com',
                'bumiairlines.com',
                'oziskies.com',
                'sakuraairways.com'
            ]
            
            role_target = 'staf' if domain in allowed_staff_domains else 'member'
            
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {role_target} WHERE email = %s", [email])
                if not cursor.fetchone():
                    messages.error(request, f"Login gagal. Email Anda menggunakan domain {role_target}, tetapi tidak terdaftar di sistem {role_target}.")
                    return render(request, 'login.html')

            login(request, user)
            request.session['user_role'] = role_target
            return redirect('main:dashboard')
        else:
            messages.error(request, 'Email atau password salah.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('main:login')

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

            if role == 'staf':
                domain = email.split('@')[-1]
                allowed_domains = [
                    'nusantaraair.com',
                    'lionsky.com',
                    'bumiairlines.com',
                    'oziskies.com',
                    'sakuraairways.com'
                ]
                if domain not in allowed_domains:
                    messages.error(request, f'Email staf harus menggunakan domain resmi ({", ".join(allowed_domains)}).')
                    return redirect('main:register')

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pengguna WHERE email = %s", [email])
                if cursor.fetchone():
                    messages.error(request, 'Email sudah terdaftar.')
                    return redirect('main:register')

                tier_id = None
                if role == 'member':
                    cursor.execute("SELECT id_tier FROM tier ORDER BY id_tier LIMIT 1")
                    row = cursor.fetchone()
                    if not row:
                        messages.error(request, 'Tier belum tersedia. Hubungi admin untuk menambahkan data tier.')
                        return redirect('main:register')
                    tier_id = row[0]

                maskapai_code = None
                if role == 'staf':
                    cursor.execute("SELECT kode_maskapai FROM maskapai WHERE kode_maskapai = %s", [data.get('kode_maskapai')])
                    row = cursor.fetchone()
                    if not row:
                        messages.error(request, 'Kode maskapai tidak valid.')
                        return redirect('main:register')
                    maskapai_code = row[0]

                cursor.execute("""
                    INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    email,
                    make_password(password),
                    data.get('salutation'),
                    data.get('first_mid_name'),
                    data.get('last_name'),
                    data.get('country_code'),
                    data.get('phone_number'),
                    data.get('dob'),
                    data.get('nationality')
                ])

                if role == 'member':
                    cursor.execute("""
                        INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [
                        email,
                        _generate_member_number(),
                        timezone.now().date(),
                        tier_id,
                        0,
                        0
                    ])
                else:
                    cursor.execute("""
                        INSERT INTO staf (email, id_staf, kode_maskapai)
                        VALUES (%s, %s, %s)
                    """, [
                        email,
                        _generate_staf_id(),
                        maskapai_code
                    ])

            messages.success(request, 'Registrasi berhasil. Silakan login.')
            return redirect('main:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai ORDER BY nama_maskapai")
        maskapai_list = dictfetchall(cursor)
        
    return render(request, 'register.html', {
        'form': form,
        'maskapai_list': maskapai_list
    })

@login_required(login_url='main:login')
def dashboard_view(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        messages.error(request, 'Data pengguna tidak ditemukan. Silakan login ulang.')
        return redirect('main:login')

    role = request.session.get('user_role')
    
    if not role:
        member = _get_member(request)
        staf = _get_staf(request)
        role = 'member' if member else 'staf' if staf else 'guest'
    else:
        member = _get_member(request) if role == 'member' else None
        staf = _get_staf(request) if role == 'staf' else None
        
        if role == 'member' and not member:
            messages.error(request, 'Profil member tidak ditemukan.')
            return redirect('main:login')
        if role == 'staf' and not staf:
            messages.error(request, 'Profil staf tidak ditemukan.')
            return redirect('main:login')

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
            'tier': member.tier_nama if hasattr(member, 'tier_nama') else member.id_tier_id,
            'total_miles': member.total_miles or 0,
            'award_miles': member.award_miles or 0,
            'tanggal_bergabung': member.tanggal_bergabung,
        })
    elif role == 'staf' and staf:
        context.update({
            'id_staf': staf.id_staf,
            'maskapai': staf.kode_maskapai_id,
            'klaim_menunggu': 0,
            'klaim_disetujui': 0,
            'klaim_ditolak': 0,
        })
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT status_penerimaan, COUNT(*) 
                FROM claim_missing_miles 
                WHERE maskapai = %s 
                GROUP BY status_penerimaan
            """, [staf.kode_maskapai_id])
            for status, count in cursor.fetchall():
                if status == 'Menunggu':
                    context['klaim_menunggu'] = count
                elif status == 'Disetujui':
                    context['klaim_disetujui'] = count
                elif status == 'Ditolak':
                    context['klaim_ditolak'] = count

    return render(request, 'dashboard.html', context)

@login_required(login_url='main:login')
def profile_view(request):
    pengguna = _get_pengguna(request)
    if not pengguna:
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('main:login')

    member = _get_member(request)
    staf = _get_staf(request)
    role = 'member' if member else 'staf' if staf else 'guest'

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = ProfileForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE pengguna 
                        SET salutation = %s, first_mid_name = %s, last_name = %s, 
                            country_code = %s, mobile_number = %s, tanggal_lahir = %s, 
                            kewarganegaraan = %s
                        WHERE email = %s
                    """, [
                        data.get('salutation'),
                        data.get('first_mid_name'),
                        data.get('last_name'),
                        data.get('country_code'),
                        data.get('phone_number'),
                        data.get('dob'),
                        data.get('nationality'),
                        pengguna.email
                    ])

                    if role == 'staf' and staf:
                        kode_maskapai = data.get('kode_maskapai')
                        if kode_maskapai:
                            cursor.execute("SELECT 1 FROM maskapai WHERE kode_maskapai = %s", [kode_maskapai])
                            if not cursor.fetchone():
                                messages.error(request, 'Kode maskapai tidak valid.')
                                return redirect('main:profile')
                            
                            cursor.execute("UPDATE staf SET kode_maskapai = %s WHERE email = %s", [kode_maskapai, pengguna.email])

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
            
            if not (check_password(old_password, request.user.password) or request.user.password == old_password):
                messages.error(request, 'Password lama salah.')
            elif new_password != confirm_password:
                messages.error(request, 'Konfirmasi password baru tidak cocok.')
            else:
                hashed_password = make_password(new_password)
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE pengguna SET password = %s WHERE email = %s", [hashed_password, pengguna.email])
                
                request.user.password = hashed_password
                update_session_auth_hash(request, request.user)
                
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

@login_required(login_url='main:login')
def member_list_view(request):
    staf = _get_staf(request)
    if not staf:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        member_id = request.POST.get('member_id')
        
        with connection.cursor() as cursor:
            if action == 'delete' and member_id:
                cursor.execute("SELECT email FROM member WHERE nomor_member = %s", [member_id])
                row = cursor.fetchone()
                if row:
                    email = row[0]
                    cursor.execute("DELETE FROM member WHERE nomor_member = %s", [member_id])
                    cursor.execute("DELETE FROM pengguna WHERE email = %s", [email])
                    messages.success(request, 'Member berhasil dihapus.')
            
            elif action == 'edit' and member_id:
                cursor.execute("SELECT email FROM member WHERE nomor_member = %s", [member_id])
                row = cursor.fetchone()
                if row:
                    email = row[0]
                    tier_value = request.POST.get('tier')
                    cursor.execute("SELECT id_tier FROM tier WHERE nama = %s OR id_tier = %s LIMIT 1", [tier_value, tier_value])
                    tier_row = cursor.fetchone()
                    if not tier_row:
                        messages.error(request, 'Tier tidak valid.')
                        return redirect('main:member_list')
                    tier_id = tier_row[0]

                    cursor.execute("""
                        UPDATE pengguna 
                        SET salutation = %s, first_mid_name = %s, last_name = %s, 
                            country_code = %s, mobile_number = %s, kewarganegaraan = %s, 
                            tanggal_lahir = %s
                        WHERE email = %s
                    """, [
                        request.POST.get('salutation'),
                        request.POST.get('first_mid_name'),
                        request.POST.get('last_name'),
                        request.POST.get('country_code'),
                        request.POST.get('phone_number'),
                        request.POST.get('nationality'),
                        request.POST.get('dob'),
                        email
                    ])
                    cursor.execute("UPDATE member SET id_tier = %s WHERE nomor_member = %s", [tier_id, member_id])
                    messages.success(request, 'Data member berhasil diperbarui.')
            
            elif action == 'create':
                email = request.POST.get('email')
                password = request.POST.get('password')
                
                cursor.execute("SELECT 1 FROM pengguna WHERE email = %s", [email])
                if cursor.fetchone():
                    messages.error(request, 'Email sudah terdaftar.')
                    return redirect('main:member_list')

                cursor.execute("SELECT id_tier FROM tier ORDER BY id_tier LIMIT 1")
                tier_row = cursor.fetchone()
                if not tier_row:
                    messages.error(request, 'Tier belum tersedia. Hubungi admin.')
                    return redirect('main:member_list')
                tier_id = tier_row[0]

                cursor.execute("""
                    INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, kewarganegaraan, tanggal_lahir)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    email,
                    make_password(password),
                    request.POST.get('salutation'),
                    request.POST.get('first_mid_name'),
                    request.POST.get('last_name'),
                    request.POST.get('country_code'),
                    request.POST.get('phone_number'),
                    request.POST.get('nationality'),
                    request.POST.get('dob')
                ])
                cursor.execute("""
                    INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [
                    email,
                    _generate_member_number(),
                    timezone.now().date(),
                    tier_id,
                    0,
                    0
                ])
                messages.success(request, 'Member baru berhasil ditambahkan.')
        return redirect('main:member_list')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.*, p.*, t.nama as tier_nama
            FROM member m
            JOIN pengguna p ON m.email = p.email
            JOIN tier t ON m.id_tier = t.id_tier
            ORDER BY m.tanggal_bergabung DESC
        """)
        rows = dictfetchall(cursor)
    
    members = []
    for row in rows:
        members.append(SimpleNamespace(
            id=row['nomor_member'],
            member_number=row['nomor_member'],
            full_name=f"{row['salutation']} {row['first_mid_name']} {row['last_name']}",
            user=SimpleNamespace(email=row['email']),
            tier=row['tier_nama'],
            total_miles=row['total_miles'] or 0,
            award_miles=row['award_miles'] or 0,
            join_date=row['tanggal_bergabung'],
            salutation=row['salutation'],
            first_mid_name=row['first_mid_name'],
            last_name=row['last_name'],
            nationality=row['kewarganegaraan'],
            country_code=row['country_code'],
            phone_number=row['mobile_number'],
            dob=row['tanggal_lahir'],
        ))
    context = {
        'role': 'staf',
        'members': members,
    }
    return render(request, 'member_list.html', context)

@login_required(login_url='main:login')
def identity_list_view(request):
    member = _get_member(request)
    if not member:
        messages.error(request, 'Akses ditolak.')
        return redirect('main:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        identity_id = request.POST.get('identity_id')
        
        with connection.cursor() as cursor:
            if action == 'delete' and identity_id:
                cursor.execute("DELETE FROM identitas WHERE nomor = %s AND email_member = %s", [identity_id, member.email.email])
                messages.success(request, 'Identitas berhasil dihapus.')
            elif action == 'edit' and identity_id:
                cursor.execute("""
                    UPDATE identitas 
                    SET jenis = %s, negara_penerbit = %s, tanggal_terbit = %s, tanggal_habis = %s
                    WHERE nomor = %s AND email_member = %s
                """, [
                    request.POST.get('jenis'),
                    request.POST.get('negara_penerbit'),
                    request.POST.get('tanggal_terbit'),
                    request.POST.get('tanggal_habis'),
                    identity_id,
                    member.email.email
                ])
                messages.success(request, 'Identitas berhasil diperbarui.')
            elif action == 'create':
                no_dok = request.POST.get('no_dokumen')
                cursor.execute("SELECT 1 FROM identitas WHERE nomor = %s", [no_dok])
                if cursor.fetchone():
                    messages.error(request, 'Nomor dokumen sudah terdaftar di sistem.')
                else:
                    cursor.execute("""
                        INSERT INTO identitas (email_member, nomor, jenis, negara_penerbit, tanggal_terbit, tanggal_habis)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [
                        member.email.email,
                        no_dok,
                        request.POST.get('jenis'),
                        request.POST.get('negara_penerbit'),
                        request.POST.get('tanggal_terbit'),
                        request.POST.get('tanggal_habis'),
                    ])
                    messages.success(request, 'Identitas baru berhasil ditambahkan.')
        return redirect('main:identity_list')

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM identitas WHERE email_member = %s", [member.email.email])
        rows = dictfetchall(cursor)
        
    identities = [
        SimpleNamespace(
            id=row['nomor'],
            no_dokumen=row['nomor'],
            jenis=row['jenis'],
            negara_penerbit=row['negara_penerbit'],
            tanggal_terbit=row['tanggal_terbit'],
            tanggal_habis=row['tanggal_habis'],
        )
        for row in rows
    ]
    context = {
        'role': 'member',
        'identities': identities,
    }
    return render(request, 'identity_list.html', context)