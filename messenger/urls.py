from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:room_slug>/', views.private_room, name='private_room'),
]