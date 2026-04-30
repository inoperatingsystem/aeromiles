from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        from django.contrib.auth.models import update_last_login
        import django.contrib.auth.models

        # Disconnect using the exact dispatch_uid used by Django's auth app
        user_logged_in.disconnect(update_last_login, dispatch_uid='update_last_login')
        
        # Monkey-patch as a foolproof fallback
        django.contrib.auth.models.update_last_login = lambda sender, user, **kwargs: None
