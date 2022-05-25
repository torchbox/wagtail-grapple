import graphene
from graphene_django import DjangoObjectType
from wagtailmedia.models import Media, get_media_model

from ..registry import registry
from ..utils import get_media_item_url, resolve_queryset
from .collections import CollectionObjectType
from .structures import QuerySetList


class MediaObjectType(DjangoObjectType):
    class Meta:
        model = Media
        exclude = ("tags",)

    url = graphene.String(required=True)
    collection = graphene.Field(lambda: CollectionObjectType, required=True)

    def resolve_url(self, info, **kwargs):
        """
        Get Media file url.
        """
        return get_media_item_url(self)


def MediaQuery():
    registry.media[Media] = MediaObjectType
    mdl = get_media_model()
    mdl_type = get_media_type()

    class Mixin:
        media_item = graphene.Field(mdl_type, id=graphene.ID())
        media = QuerySetList(
            graphene.NonNull(mdl_type), enable_search=True, required=True
        )

        def resolve_media_item(self, info, id, **kwargs):
            """Returns a media item given the id, if in a public collection"""
            try:
                return mdl.objects.filter(
                    collection__view_restrictions__isnull=True
                ).get(pk=id)
            except BaseException:
                return None

        def resolve_media(self, info, **kwargs):
            """Return only the items with no collection or in a public collection"""
            qs = mdl.objects.filter(collection__view_restrictions__isnull=True)
            return resolve_queryset(qs, info, **kwargs)

        def resolve_media_type(self, info, **kwargs):
            return mdl_type

    return Mixin


def get_media_type():
    registry.media[Media] = MediaObjectType
    mdl = get_media_model()
    return registry.media[mdl]
