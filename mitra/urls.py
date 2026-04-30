from django.urls import path
from . import views

app_name = 'mitra'  

urlpatterns = [
    path('partners/',                          views.mitra_list,   name='mitra_list'),
    path('partners/create/',                   views.mitra_create, name='mitra_create'),
    path('partners/<str:email_mitra>/edit/',   views.mitra_update, name='mitra_update'),
    path('partners/<str:email_mitra>/delete/', views.mitra_delete, name='mitra_delete'),
    path('', views.mitra_list, name='list'),
]