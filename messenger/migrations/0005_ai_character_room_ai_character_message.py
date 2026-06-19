from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('messenger', '0004_private_group_room_private_group_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='ai_character_room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='名前')),
                ('gender', models.CharField(choices=[('male', '男性'), ('female', '女性'), ('other', 'その他')], max_length=10)),
                ('age', models.PositiveSmallIntegerField(verbose_name='年齢')),
                ('personality', models.TextField(verbose_name='詳細設定')),
                ('icon', models.ImageField(blank=True, null=True, upload_to='ai_icons/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_rooms', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ai_character_message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'ユーザー'), ('assistant', 'AI')], max_length=10)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='messenger.ai_character_room')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
