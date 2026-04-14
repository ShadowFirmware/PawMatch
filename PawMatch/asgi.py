"""
ASGI config for PawMatch project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PawMatch.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from chat_app import routing as chat_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # AllowedHostsOriginValidator removido: en dev causa 404 ocasionales cuando
    # el frontend corre en un puerto diferente (ej. localhost:5173).
    # La autenticación por token en el consumer ya protege los WebSockets.
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_routing.websocket_urlpatterns
        )
    ),
})
