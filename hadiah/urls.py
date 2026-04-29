from django.urls import path
from . import views

app_name = 'hadiah'

urlpatterns = [
    path('manage-rewards/',                          views.hadiah_list,   name='hadiah_list'),
    path('manage-rewards/create/',                   views.hadiah_create, name='hadiah_create'),
    path('manage-rewards/<str:kode_hadiah>/edit/',   views.hadiah_update, name='hadiah_update'),
    path('manage-rewards/<str:kode_hadiah>/delete/', views.hadiah_delete, name='hadiah_delete'),
    path('', views.hadiah_list, name='list'),
]