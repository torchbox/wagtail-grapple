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

    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    descendants = graphene.List(lambda: CollectionObjectType, required=True)
    ancestors = graphene.List(lambda: CollectionObjectType, required=True)

    def resolve_descendants(self, info, **kwargs):
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
