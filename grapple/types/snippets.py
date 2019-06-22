import graphene
from django.contrib.contenttypes.models import ContentType
from graphene_django.types import DjangoObjectType
from graphql.execution.base import ResolveInfo
from wagtail.snippets.models import get_snippet_models

from ..registry import registry
from ..utils import resolve_queryset
from .structures import QuerySetList


def SnippetsQuery():
    if registry.snippets:

        class Snippet(graphene.Union):
            class Meta:
                types = registry.snippets.types

        class Mixin:
            snippets = graphene.List(Snippet)
            # Return all snippets.
            def resolve_snippets(self, info, **kwargs):
                snippet_objects = []
                for snippet in registry.snippets:
                    for object in snippet._meta.model.objects.all():
                        snippet_objects.append(object)

                return snippet_objects

        return Mixin

    else:

        class Mixin:
            pass

        return Mixin
