import graphene
from graphene_django import DjangoObjectType
from wagtailmedia.models import Media
from ..utils import get_media_item_url, resolve_queryset


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
