from django import forms
from .models import Pengguna


ROLE_CHOICES = [
    ('member', 'Member'),
    ('staf', 'Staf'),
]


class RegisterForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    salutation = forms.ChoiceField(choices=Pengguna.SALUTATION_CHOICES)
    first_mid_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    country_code = forms.CharField(max_length=5)
    phone_number = forms.CharField(max_length=20)
    dob = forms.DateField()
    nationality = forms.CharField(max_length=50)
    kode_maskapai = forms.CharField(max_length=10, required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Password dan konfirmasi password tidak cocok.')

        return cleaned_data


class ProfileForm(forms.Form):
    salutation = forms.ChoiceField(choices=Pengguna.SALUTATION_CHOICES)
    first_mid_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    country_code = forms.CharField(max_length=5)
    phone_number = forms.CharField(max_length=20)
    dob = forms.DateField()
    nationality = forms.CharField(max_length=50)
    kode_maskapai = forms.CharField(max_length=10, required=False)


class IdentitasForm(forms.Form):
    no_dokumen = forms.CharField(max_length=50)
    jenis = forms.ChoiceField(choices=[('Paspor', 'Paspor'), ('KTP', 'KTP'), ('SIM', 'SIM')])
    negara_penerbit = forms.CharField(max_length=50)
    tanggal_terbit = forms.DateField()
    tanggal_habis = forms.DateField()
