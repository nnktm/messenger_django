from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    private_room as PrivateRoom,
    private_group_room as PrivateGroupRoom,
    Profile,
    get_avatar_url_for_user,
    get_group_icon_url_for_room,
)
from .forms import ProfileEditForm, GroupCreateForm

@login_required
def index(request):
    private_rooms = PrivateRoom.objects.filter(
        Q(member_1=request.user) | Q(member_2=request.user)
    ).order_by('-created_at')
    group_rooms = request.user.group_rooms.order_by('-created_at')
    other_usernames = list(
        User.objects.exclude(pk=request.user.pk)
        .order_by('username')
        .values_list('username', flat=True)
    )
    return render(request, 'messenger/index.html', {
        'private_message_rooms': private_rooms,
        'group_rooms': group_rooms,
        'other_usernames': other_usernames,
    })

@login_required
def create_group(request):
    other_usernames = list(
        User.objects.exclude(pk=request.user.pk)
        .order_by('username')
        .values_list('username', flat=True)
    )
    if request.method == 'POST':
        form = GroupCreateForm(request.POST, request.FILES, creator=request.user)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'グループ「{room.name}」を作成しました。')
            return redirect('private_group_room', room_id=room.pk)
    else:
        form = GroupCreateForm(creator=request.user)

    return render(request, 'messenger/create_group.html', {
        'form': form,
        'other_usernames': other_usernames,
    })

@login_required
def private_group_room(request, room_id):
    group_room = get_object_or_404(
        PrivateGroupRoom.objects.prefetch_related('members'),
        pk=room_id,
        members=request.user,
    )
    group_messages = group_room.messages.select_related('sender').order_by('created_at')[:200]
    return render(request, 'messenger/private_group_room.html', {
        'group_room': group_room,
        'group_icon_url': get_group_icon_url_for_room(group_room),
        'members': group_room.members.order_by('username'),
        'initial_messages': [
            {
                'username': m.sender.username,
                'message': m.content,
                'avatar_url': get_avatar_url_for_user(m.sender),
                'created_at': m.created_at.isoformat(),
            }
            for m in group_messages
        ],
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
        'other_user': other_user,
        'other_user_avatar_url': get_avatar_url_for_user(other_user),
        'initial_messages': [
            {
                'username': m.sender.username,
                'message': m.content,
                'avatar_url': get_avatar_url_for_user(m.sender),
                'created_at': m.created_at.isoformat(),
            }
            for m in private_messages
        ],
    })


@login_required
def profile(request, username=None):
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)

    is_own_profile = profile_user == request.user
    profile_obj, _ = Profile.objects.get_or_create(user=profile_user)

    if is_own_profile and request.method == 'POST':
        form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=profile_obj,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィールを更新しました。')
            return redirect('profile')
    elif is_own_profile:
        form = ProfileEditForm(instance=profile_obj, user=request.user)
    else:
        form = None

    return render(request, 'messenger/profile.html', {
        'profile_user': profile_user,
        'profile': profile_obj,
        'is_own_profile': is_own_profile,
        'form': form,
    })
