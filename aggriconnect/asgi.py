import os

from channels.routing import URLRouter, ProtocolTypeRouter
from aggriconnect.middleware import JwtAuthMiddlewareStack
from django.core.asgi import get_asgi_application
import wholesaler.routes

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aggriconnect.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":JwtAuthMiddlewareStack(
        URLRouter(
            wholesaler.routes.websocket_urlpatterns
        )
    )
})
