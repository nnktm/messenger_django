from django import forms
from django.contrib.auth.models import User

from .models import Profile


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
