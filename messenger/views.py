from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    private_room as PrivateRoom,
    private_group_room as PrivateGroupRoom,
    ai_character_room as AICharacterRoom,
    ai_character_message as AICharacterMessage,
    open_room as OpenRoom,
    open_room_visit as OpenRoomVisit,
    Profile,
    get_avatar_url_for_user,
    get_group_icon_url_for_room,
    get_ai_icon_url_for_room,
)
from .forms import ProfileEditForm, GroupCreateForm, AICharacterCreateForm, OpenRoomCreateForm


def record_open_room_visit(user, room):
    OpenRoomVisit.objects.update_or_create(user=user, room=room)


@login_required
def index(request):
    private_rooms = PrivateRoom.objects.filter(
        Q(member_1=request.user) | Q(member_2=request.user)
    ).select_related('member_1', 'member_2').order_by('-created_at')
    group_rooms = request.user.group_rooms.order_by('-created_at')
    other_usernames = list(
        User.objects.exclude(pk=request.user.pk)
        .order_by('username')
        .values_list('username', flat=True)
    )
    private_room_items = []
    for room in private_rooms:
        other_user = room.member_2 if room.member_1_id == request.user.pk else room.member_1
        private_room_items.append({
            'other_user': other_user,
            'avatar_url': get_avatar_url_for_user(other_user),
        })
    group_room_items = [
        {
            'room': room,
            'icon_url': get_group_icon_url_for_room(room),
        }
        for room in group_rooms
    ]
    ai_room_items = [
        {
            'room': room,
            'icon_url': get_ai_icon_url_for_room(room),
        }
        for room in request.user.ai_rooms.order_by('-created_at')
    ]
    visited_open_rooms = (
        OpenRoomVisit.objects.filter(user=request.user)
        .select_related('room')
        .order_by('-visited_at')
    )
    open_room_items = [{'room': visit.room} for visit in visited_open_rooms]
    open_room_search = [
        {'id': room.pk, 'name': room.name}
        for room in OpenRoom.objects.order_by('-created_at')
    ]
    return render(request, 'messenger/index.html', {
        'private_room_items': private_room_items,
        'group_room_items': group_room_items,
        'ai_room_items': ai_room_items,
        'open_room_items': open_room_items,
        'open_room_search': open_room_search,
        'other_usernames': other_usernames,
    })

@login_required
def create_open_room(request):
    if request.method == 'POST':
        form = OpenRoomCreateForm(request.POST)
        if form.is_valid():
            room = form.save()
            record_open_room_visit(request.user, room)
            messages.success(request, f'公開ルーム「{room.name}」を作成しました。')
            return redirect('open_room', room_id=room.pk)
    else:
        form = OpenRoomCreateForm()

    return render(request, 'messenger/create_open_room.html', {'form': form})


@login_required
def open_room(request, room_id):
    open_room_obj = get_object_or_404(OpenRoom, pk=room_id)
    record_open_room_visit(request.user, open_room_obj)
    open_messages = open_room_obj.messages.select_related('sender').order_by('created_at')[:200]
    return render(request, 'messenger/open_room.html', {
        'open_room': open_room_obj,
        'initial_messages': [
            {
                'username': m.sender.username,
                'message': m.content,
                'avatar_url': get_avatar_url_for_user(m.sender),
                'created_at': m.created_at.isoformat(),
            }
            for m in open_messages
        ],
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
def create_ai_room(request):
    if request.method == 'POST':
        form = AICharacterCreateForm(request.POST, request.FILES, owner=request.user)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'AIキャラクター「{room.name}」を作成しました。')
            return redirect('ai_room', room_id=room.pk)
    else:
        form = AICharacterCreateForm(owner=request.user)

    return render(request, 'messenger/create_ai_room.html', {'form': form})

@login_required
def ai_room(request, room_id):
    ai_room_obj = get_object_or_404(AICharacterRoom, pk=room_id, owner=request.user)
    ai_messages = ai_room_obj.messages.order_by('created_at')[:200]
    user_avatar_url = get_avatar_url_for_user(request.user)
    ai_icon_url = get_ai_icon_url_for_room(ai_room_obj)
    return render(request, 'messenger/ai_room.html', {
        'ai_room': ai_room_obj,
        'ai_icon_url': ai_icon_url,
        'initial_messages': [
            {
                'message': m.content,
                'username': ai_room_obj.name if m.role == AICharacterMessage.Role.ASSISTANT else request.user.username,
                'avatar_url': ai_icon_url if m.role == AICharacterMessage.Role.ASSISTANT else user_avatar_url,
                'created_at': m.created_at.isoformat(),
                'is_ai': m.role == AICharacterMessage.Role.ASSISTANT,
            }
            for m in ai_messages
        ],
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
