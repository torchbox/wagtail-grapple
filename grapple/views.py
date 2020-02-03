from django.utils.functional import cached_property
from graphene_django.views import GraphQLView

from .loaders import create_model_loader

# Custom view used to bind Dataloader to Request lifetime and not server lifetime.
class GrappleContext:
    def __init__(self, request):
        self.request = request
        self.model_loader = create_model_loader({})


class GrappleView(GraphQLView):
    def get_context(self, request):
        return GrappleContext(request)
