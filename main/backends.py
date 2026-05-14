from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.db import connection
from .models import Pengguna
from .utils import dictfetchone

class PenggunaAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT aeromiles.fn_verifikasi_login(%s)", [username])
            row = cursor.fetchone()
            
            if row:
                hashed_password = row[0]
                if check_password(password, hashed_password) or hashed_password == password:
                    cursor.execute(
                        "SELECT * FROM pengguna WHERE LOWER(email) = LOWER(%s)", 
                        [username]
                    )
                    user_row = dictfetchone(cursor)
                    if user_row:
                        return Pengguna(**user_row)
        return None

    def get_user(self, user_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pengguna WHERE email = %s", [user_id])
            row = dictfetchone(cursor)
            if row:
                return Pengguna(**row)
        return None
