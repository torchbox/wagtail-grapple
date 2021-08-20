import os
import django

from channels.routing import URLRouter
from .urls import channels_urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grapple.settings")

application_config = {"websocket": URLRouter(channels_urls)}

if django.VERSION < (2, 3):
    from channels.http import AsgiHandler
    from channels.routing import ProtocolTypeRouter

    django.setup()

    application_config["http"] = AsgiHandler()

else:
    from django.core.asgi import get_asgi_application
    from channels.routing import ProtocolTypeRouter

    application = ProtocolTypeRouter(
        {
            "http": get_asgi_application(),
        }
    )


application = ProtocolTypeRouter(application_config)
