from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import SESSION_KEY
from .models import Pengguna

from django.db import connection
from .utils import dictfetchone

def get_pengguna(request):
    if not hasattr(request, '_cached_user'):
        user_id = request.session.get(SESSION_KEY)
        if user_id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM pengguna WHERE email = %s", [user_id])
                row = dictfetchone(cursor)
                if row:
                    request._cached_user = Pengguna(**row)
                else:
                    request._cached_user = AnonymousUser()
        else:
            request._cached_user = AnonymousUser()
    return request._cached_user

class PenggunaAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = SimpleLazyObject(lambda: get_pengguna(request))
        return self.get_response(request)
