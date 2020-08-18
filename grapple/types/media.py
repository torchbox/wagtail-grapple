import graphene

from graphene_django import DjangoObjectType

from wagtailmedia.models import Media, get_media_model

from ..registry import registry
from ..utils import get_media_item_url, resolve_queryset
from .structures import QuerySetList


class MediaObjectType(DjangoObjectType):
    class Meta:
        model = Media
        exclude_fields = ("tags",)

    url = graphene.String(required=True)

    def resolve_url(self, info):
        """
        Get Media file url.
        """
        return get_media_item_url(self)


def MediaQuery():
    registry.media[Media] = MediaObjectType
    mdl = get_media_model()
    model_type = registry.media[mdl]

    class Mixin:
        media = QuerySetList(
            graphene.NonNull(model_type), enable_search=True, required=True
        )

        # Return all pages, ideally specific.
        def resolve_media(self, info, **kwargs):
            return resolve_queryset(mdl.objects.all(), info, **kwargs)

    return Mixin


def get_media_type():
    registry.media[Media] = MediaObjectType
    mdl = get_media_model()
    return registry.media[mdl]
