from django.urls import path
from pourover import consumers

websocket_urlpatterns = [
    path('pourover/data', consumers.MyConsumer.as_asgi()),
]
