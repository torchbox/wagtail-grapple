from django.shortcuts import render
from django.urls import path, reverse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from .settings import grapple_settings, has_channels


def graphiql(request):
    graphiql_settings = {
        "REACT_VERSION": "18.2.0",
        "GRAPHIQL_VERSION": "2.0.13",
        "endpointURL": reverse("grapple_graphql"),
        "supports_subscriptions": has_channels,
    }
    if has_channels:
        # TODO: The version below is fixed at 0.8.3 and could be upgraded, but
        # this need to be done with caution as 0.9.x breaks GraphiQL 1.4.2.
        graphiql_settings["SUBSCRIPTIONS_TRANSPORT_VERSION"] = "0.8.3"
        graphiql_settings["subscriptionsEndpoint"] = "ws://localhost:8000/subscriptions"

    return render(request, "grapple/graphiql.html", graphiql_settings)


# Traditional URL routing
urlpatterns = [
    path("graphql/", csrf_exempt(GraphQLView.as_view()), name="grapple_graphql")
]

if grapple_settings.EXPOSE_GRAPHIQL:
    urlpatterns.append(path("graphiql/", graphiql, name="grapple_graphiql"))
