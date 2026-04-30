from django.urls import path
from . import views

app_name = 'klaim'

urlpatterns = [
    # Member
    path('',                              views.member_klaim_list,   name='member_list'),
    path('create/',                       views.member_klaim_create, name='member_create'),
    path('<int:no_klaim>/edit/',          views.member_klaim_update, name='member_update'),
    path('<int:no_klaim>/delete/',        views.member_klaim_delete, name='member_delete'),

    # Staf
    path('manage/',                       views.staf_klaim_list,     name='staf_list'),
    path('manage/<int:no_klaim>/action/', views.staf_klaim_action,   name='staf_action'),
]
