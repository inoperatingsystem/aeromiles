from django.urls import path
from . import views

app_name = 'package'

urlpatterns = [
    # Member
    path('', views.member_package_list, name='list'),
    path('<str:id_paket>/buy/', views.member_package_buy, name='buy'),
]
