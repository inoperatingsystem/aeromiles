from django.urls import path
from . import views

app_name = 'redeem'

urlpatterns = [
    # Member
    path('', views.member_redeem_list, name='member_redeem_list'),
    path('<str:kode_hadiah>/', views.member_redeem_create, name='member_redeem_create'),
]
