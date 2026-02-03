from django.urls import path
from . import consumers
websocket_urlpatterns = [
    path("ws/bidding/<int:l_id>/",consumers.MyBiddingConsumers.as_asgi())
]