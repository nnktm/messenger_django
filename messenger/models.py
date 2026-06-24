from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


def avatar_upload_path(instance, filename):
    return f'avatars/{instance.user.pk}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)

    def __str__(self):
        return f'Profile({self.user.username})'

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return settings.DEFAULT_AVATAR_URL


def get_avatar_url_for_user(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile.avatar_url


class private_room(models.Model):
    member_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_rooms_as_m1')
    member_2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_rooms_as_m2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['member_1', 'member_2'], name='unique_private_room'),
        ]
    def __str__(self):
        return f"{self.member_1.username} and {self.member_2.username}"

class private_message(models.Model):
    room = models.ForeignKey(private_room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} @ {self.room.member_1.username} and {self.room.member_2.username}: {self.content[:30]}"

class private_group_room(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ImageField(upload_to='group_icons/', blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    members = models.ManyToManyField(User, related_name='group_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Group Room({self.name})"

    @property
    def icon_display_url(self):
        if self.icon:
            return self.icon.url
        if self.icon_url:
            return self.icon_url
        return settings.DEFAULT_AVATAR_URL


def get_group_icon_url_for_room(room):
    return room.icon_display_url

class private_group_message(models.Model):
    room = models.ForeignKey(private_group_room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} @ {self.room.name}: {self.content[:30]}"


class ai_character_room(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', '男性'
        FEMALE = 'female', '女性'
        OTHER = 'other', 'その他'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_rooms')
    name = models.CharField(max_length=100, verbose_name='名前')
    gender = models.CharField(max_length=10, choices=Gender.choices)
    age = models.PositiveSmallIntegerField(verbose_name='年齢')
    personality = models.TextField(verbose_name='詳細設定')
    icon = models.ImageField(upload_to='ai_icons/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI({self.name})"

    @property
    def icon_display_url(self):
        if self.icon:
            return self.icon.url
        return settings.DEFAULT_AVATAR_URL

    def build_system_prompt(self):
        gender_label = self.get_gender_display()
        return (
            f'あなたは「{self.name}」というキャラクターです。\n'
            f'性別: {gender_label}\n'
            f'年齢: {self.age}歳\n'
            f'詳細設定:\n{self.personality}\n\n'
            '上記の設定に従い、キャラクターとして一貫した口調・性格で、'
            'ユーザーと自然な日本語で会話してください。'
        )


def get_ai_icon_url_for_room(room):
    return room.icon_display_url


class ai_character_message(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'ユーザー'
        ASSISTANT = 'assistant', 'AI'

    room = models.ForeignKey(ai_character_room, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} @ {self.room.name}: {self.content[:30]}"


class open_room(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Open Room({self.name})"


class open_room_visit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='open_room_visits')
    room = models.ForeignKey(open_room, on_delete=models.CASCADE, related_name='visits')
    visited_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'room'], name='unique_open_room_visit'),
        ]

    def __str__(self):
        return f"{self.user.username} visited {self.room.name}"


class open_room_message(models.Model):
    room = models.ForeignKey(open_room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_open_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} @ {self.room.name}: {self.content[:30]}"