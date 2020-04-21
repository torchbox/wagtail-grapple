from wagtail.core.models import Collection
from wagtail.core import hooks
from graphene_django.types import DjangoObjectType
import graphene
from ..registry import registry
from ..utils import resolve_queryset
from .structures import QuerySetList


class CollectionObjectType(DjangoObjectType):
    """
    Collection type
    """

    class Meta:
        model = Collection

    id = graphene.ID()
    name = graphene.String()
    descendants = graphene.List(lambda: CollectionObjectType)
    ancestors = graphene.List(lambda: CollectionObjectType)
    contents = graphene.List(lambda: CollectionObjectType)

    def resolve_contents(self, info):
        return list([
            hook(self)
            for hook in hooks.get_hooks("describe_collection_contents")
        ])

    def resolve_descendants(self, info):
        return self.get_descendants()

    def resolve_ancestors(self, info):
        return self.get_ancestors()


def CollectionsQuery():
    mdl = Collection
    mdl_type = registry.collections.get(mdl, CollectionObjectType)

    class Mixin:
        collections = QuerySetList(mdl_type, enable_search=False)
        collection_type = graphene.String()

        # Return all collections
        def resolve_collections(self, info, **kwargs):
            return resolve_queryset(mdl.objects.all(), info, **kwargs)

        def resolve_collection_type(self, info, **kwargs):
            return mdl_type

    return Mixin
