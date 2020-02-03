from django.shortcuts import render
from django.conf import settings
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from .views import GrappleView


def playground(request):
    URL = settings.BASE_URL.split("//")[1]
    graphiql_settings = {
        "endpoint": "http://" + URL + "/graphql",
        "subscriptionsEndpoint": "ws://" + URL + "/graphql",
    }

    return render(request, "grapple/playground.html", graphiql_settings)


# Traditional URL routing
urlpatterns = [
    url(r"^graphql", csrf_exempt(GrappleView.as_view(graphiql=True))),
    url(r"^playground", playground),
]
