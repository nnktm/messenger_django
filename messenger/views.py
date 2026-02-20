from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from .models import private_room as PrivateRoom, private_message
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    private_rooms = PrivateRoom.objects.filter(
        Q(member_1=request.user) | Q(member_2=request.user)
    ).order_by('-created_at')
    other_users = User.objects.exclude(pk=request.user.pk).order_by('username')
    return render(request, 'messenger/index.html', {
        'private_message_rooms': private_rooms,
        'other_users': other_users,
    })

@login_required
def private_room(request, room_slug):
    other_user = get_object_or_404(User, username=room_slug)
    if other_user == request.user:
        return redirect('index')
    u1, u2 = (request.user, other_user) if request.user.pk < other_user.pk else (other_user, request.user)
    private_room_obj, _ = PrivateRoom.objects.get_or_create(member_1=u1, member_2=u2)
    private_messages = private_room_obj.messages.select_related('sender').order_by('created_at')[:200]
    return render(request, 'messenger/private_room.html', {
        'private_room': private_room_obj,
        'private_messages': private_messages,
    })