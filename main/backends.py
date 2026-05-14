from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.db import connection
from .models import Pengguna
from .utils import dictfetchone

class PenggunaAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pengguna WHERE email = %s", [username])
            row = dictfetchone(cursor)
            
            if row:
                pengguna = Pengguna(**row)
                if check_password(password, pengguna.password) or pengguna.password == password:
                    return pengguna
        return None

    def get_user(self, user_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pengguna WHERE email = %s", [user_id])
            row = dictfetchone(cursor)
            if row:
                return Pengguna(**row)
        return None
