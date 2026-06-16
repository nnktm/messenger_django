from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import private_room as PrivateRoom, Profile, get_avatar_url_for_user
from .forms import ProfileEditForm

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