from django import forms
from django.contrib.auth.models import User

from .models import Profile, private_group_room, ai_character_room


class ProfileEditForm(forms.ModelForm):
    username = forms.CharField(label='ユーザーネーム', max_length=150)

    class Meta:
        model = Profile
        fields = ['avatar']
        labels = {
            'avatar': 'アイコン画像',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = self.user.username
        self.fields['avatar'].required = False

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('ユーザーネームを入力してください。')
        if User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
            raise forms.ValidationError('このユーザーネームは既に使われています。')
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.username = self.cleaned_data['username']
        self.user.save()
        if commit:
            profile.save()
        return profile


class GroupCreateForm(forms.Form):
    name = forms.CharField(label='グループ名', max_length=255)
    icon = forms.ImageField(label='グループアイコン', required=False)
    member_usernames = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop('creator')
        super().__init__(*args, **kwargs)

    def clean_member_usernames(self):
        raw = self.cleaned_data['member_usernames'].strip()
        if not raw:
            usernames = []
        else:
            usernames = [u.strip() for u in raw.split(',') if u.strip()]

        seen = set()
        unique_usernames = []
        for username in usernames:
            key = username.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_usernames.append(username)

        if len(unique_usernames) < 2:
            raise forms.ValidationError('メンバーは作成者以外に2人以上招待してください。')

        users = list(User.objects.filter(username__in=unique_usernames))
        found = {u.username.lower(): u for u in users}
        missing = [u for u in unique_usernames if u.lower() not in found]
        if missing:
            raise forms.ValidationError(
                f'存在しないユーザー: {", ".join(missing)}'
            )

        if self.creator.username.lower() in found:
            raise forms.ValidationError('作成者自身は招待リストに含めないでください。')

        self.invited_users = [found[u.lower()] for u in unique_usernames]
        return raw

    def save(self):
        room = private_group_room.objects.create(
            name=self.cleaned_data['name'],
            icon=self.cleaned_data.get('icon'),
        )
        room.members.add(self.creator, *self.invited_users)
        return room


class AICharacterCreateForm(forms.ModelForm):
    class Meta:
        model = ai_character_room
        fields = ['name', 'gender', 'age', 'personality', 'icon']
        labels = {
            'name': '名前',
            'gender': '性別',
            'age': '年齢',
            'personality': '詳細設定',
            'icon': 'アイコン画像',
        }
        widgets = {
            'personality': forms.Textarea(attrs={'rows': 6, 'placeholder': '性格、口調、背景設定など'}),
            'age': forms.NumberInput(attrs={'min': 1, 'max': 120}),
        }

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)
        self.fields['icon'].required = False

    def save(self, commit=True):
        room = super().save(commit=False)
        room.owner = self.owner
        if commit:
            room.save()
        return room
