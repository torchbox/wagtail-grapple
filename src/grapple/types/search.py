import graphene
from django.apps import apps
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.search.backends import get_search_backend

from ..registry import registry


def SearchQuery():
    if registry.class_models:

        class Search(graphene.Union):
            class Meta:
                types = tuple(registry.class_models.values())

        class Mixin:
            search = graphene.List(
                graphene.NonNull(Search), query=graphene.String(), required=True
            )

            # Return just one setting base on name param.
            def resolve_search(self, info, **kwargs):
                query = kwargs.get("query")
                if query:
                    s = get_search_backend()
                    results = []
                    models = [get_document_model(), get_image_model()]
                    for app in registry.apps:
                        models += apps.all_models[app].values()
                    for model in models:
                        results += s.search(query, model)
                    return results
                return None

        return Mixin

    else:

        class Mixin:
            pass

        return Mixin
