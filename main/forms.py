from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Identitas

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'salutation', 'first_mid_name', 'last_name', 'country_code', 'phone_number', 'dob', 'nationality', 'kode_maskapai']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password dan konfirmasi password tidak cocok.")
            
        if User.objects.filter(username=email).exists():
            self.add_error('email', "Email sudah terdaftar.")

        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['salutation', 'first_mid_name', 'last_name', 'country_code', 'phone_number', 'dob', 'nationality', 'kode_maskapai']

class IdentitasForm(forms.ModelForm):
    class Meta:
        model = Identitas
        fields = ['no_dokumen', 'jenis', 'negara_penerbit', 'tanggal_terbit', 'tanggal_habis']
