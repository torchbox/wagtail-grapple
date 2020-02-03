import channels
import channels_graphql_ws
from django.urls import path
from grapple.schema import schema as graphql_schema
from channels.auth import AuthMiddleware, SessionMiddleware, CookieMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter


class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    """Channels WebSocket consumer which provides GraphQL API."""

    schema = graphql_schema
    # send_keepalive_every = 42

    async def on_connect(self, payload):
        print("New client connected!")
        return []


application = ProtocolTypeRouter(
    {
        "websocket": CookieMiddleware(
            SessionMiddleware(
                AuthMiddleware(URLRouter([path("graphql", MyGraphqlWsConsumer)]))
            )
        )
    }
)
