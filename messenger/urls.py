from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='profile_user'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:room_id>/', views.private_group_room, name='private_group_room'),
    path('ai/create/', views.create_ai_room, name='create_ai_room'),
    path('ai/<int:room_id>/', views.ai_room, name='ai_room'),
    path('open/create/', views.create_open_room, name='create_open_room'),
    path('open/<int:room_id>/', views.open_room, name='open_room'),
    path('<str:room_slug>/', views.private_room, name='private_room'),
]