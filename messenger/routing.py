from django.urls import re_path
from . import consumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_name>\w+)/$', consumer.ChatConsumer.as_asgi()),
    re_path(r'^ws/chat/private/(?P<room_id>\d+)/$', consumer.PrivateChatConsumer.as_asgi()),
    re_path(r'^ws/chat/group/(?P<room_id>\d+)/$', consumer.GroupChatConsumer.as_asgi()),
    re_path(r'^ws/chat/ai/(?P<room_id>\d+)/$', consumer.AIChatConsumer.as_asgi()),
]