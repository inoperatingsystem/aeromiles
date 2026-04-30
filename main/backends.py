from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Pengguna

class PenggunaAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            pengguna = Pengguna.objects.get(email=username)
            # Support both hashed passwords (from our app) and plaintext passwords (from TA's SQL dummy data)
            if check_password(password, pengguna.password) or pengguna.password == password:
                return pengguna
        except Pengguna.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Pengguna.objects.get(email=user_id)
        except Pengguna.DoesNotExist:
            return None
