import os
from django.core.asgi import get_asgi_application

# 1. Set the settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aggriconnect.settings")

# 2. Initialize the Django ASGI application
# This call MUST happen before you import your middleware or routes
django_asgi_app = get_asgi_application()

# 3. NOW import your custom code
from channels.routing import URLRouter, ProtocolTypeRouter
from aggriconnect.middleware import JwtAuthMiddlewareStack
import wholesaler.routes

# 4. Define the protocol router
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(
            wholesaler.routes.websocket_urlpatterns
        )
    )
})