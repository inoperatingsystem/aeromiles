from django.urls import path
from . import views

app_name = 'transfer'

urlpatterns = [
    path('', views.transfer_list, name='transfer_list'),
    path('create/', views.transfer_create, name='transfer_create'),
]
