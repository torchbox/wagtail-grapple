from django.conf import settings
from django.shortcuts import render
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView
from channels.routing import route_class
from graphql_ws.django_channels import GraphQLSubscriptionConsumer


def graphiql(request):
    graphiql_settings = {
        "REACT_VERSION": "16.13.1",
        "GRAPHIQL_VERSION": "0.17.5",
        "SUBSCRIPTIONS_TRANSPORT_VERSION": "0.9.16",
        "subscriptionsEndpoint": "ws://localhost:8000/subscriptions",
        "endpointURL": "/graphql",
    }

    return render(request, "grapple/graphiql.html", graphiql_settings)


# Traditional URL routing
SHOULD_EXPOSE_GRAPHIQL = settings.DEBUG or getattr(
    settings, "GRAPPLE_EXPOSE_GRAPHIQL", False
)
urlpatterns = [url(r"^graphql", csrf_exempt(GraphQLView.as_view()))]

if SHOULD_EXPOSE_GRAPHIQL:
    urlpatterns.append(url(r"^graphiql", graphiql))

# Django Channel (v1.x) routing for subscription support
channel_routing = [route_class(GraphQLSubscriptionConsumer, path=r"^/subscriptions")]
