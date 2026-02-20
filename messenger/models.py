from enum import member
from django.db import models
from django.contrib.auth.models import User

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