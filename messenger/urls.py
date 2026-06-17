from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='profile_user'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:room_id>/', views.private_group_room, name='private_group_room'),
    path('<str:room_slug>/', views.private_room, name='private_room'),
]