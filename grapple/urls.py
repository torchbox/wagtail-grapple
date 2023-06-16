from django.shortcuts import render
from django.urls import path, reverse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from .settings import grapple_settings


def graphiql(request):
    graphiql_settings = {
        "REACT_VERSION": "18.2.0",
        "GRAPHIQL_VERSION": "2.4.7",
        "endpointURL": reverse("grapple_graphql"),
        "supports_subscriptions": False,
    }
    return render(request, "grapple/graphiql.html", graphiql_settings)


# Traditional URL routing
urlpatterns = [
    path("graphql/", csrf_exempt(GraphQLView.as_view()), name="grapple_graphql")
]

if grapple_settings.EXPOSE_GRAPHIQL:
    urlpatterns.append(path("graphiql/", graphiql, name="grapple_graphiql"))
