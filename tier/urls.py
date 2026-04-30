from django.urls import path
from . import views

app_name = 'tier'

urlpatterns = [
    # Member
    path('', views.member_tier_info, name='info'),
]
