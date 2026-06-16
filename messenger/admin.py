from django.contrib import admin
from .models import private_room, private_message, Profile

admin.site.register(private_room)
admin.site.register(private_message)
admin.site.register(Profile)
