from django.urls import path
from . import views

app_name = 'laporan'

urlpatterns = [
    # Staff
    path('', views.laporan_list, name='list'),
    path('delete/<str:transaksi_id>/', views.laporan_delete, name='delete'),
]
