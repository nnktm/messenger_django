from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('messenger', '0006_open_room_open_room_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='open_room_visit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visited_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits', to='messenger.open_room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='open_room_visits', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='open_room_visit',
            constraint=models.UniqueConstraint(fields=('user', 'room'), name='unique_open_room_visit'),
        ),
    ]
