from django.contrib import admin
from .models import private_room, private_message, Profile, private_group_room, private_group_message

admin.site.register(private_room)
admin.site.register(private_message)
admin.site.register(Profile)
admin.site.register(private_group_room)
admin.site.register(private_group_message)
