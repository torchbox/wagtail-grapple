import graphene
from graphene_django.types import DjangoObjectType

try:
    from wagtail.models import Collection
except ImportError:
    from wagtail.core.models import Collection

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
        # only return public descendant Collections
        return self.get_descendants().filter(view_restrictions__isnull=True)

    def resolve_ancestors(self, info, **kwargs):
        # only return public descendant Collections
        return self.get_ancestors().filter(view_restrictions__isnull=True)


def CollectionsQuery():
    mdl = Collection
    mdl_type = registry.collections.get(mdl, CollectionObjectType)

    class Mixin:
        collections = QuerySetList(mdl_type, enable_search=False, required=True)

        # Return all collections
        def resolve_collections(self, info, **kwargs):
            # Only return public Collections
            qs = mdl.objects.filter(view_restrictions__isnull=True)
            return resolve_queryset(qs, info, **kwargs)

        def resolve_collection_type(self, info, **kwargs):
            return mdl_type

    return Mixin
