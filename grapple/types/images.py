import os
import codecs
import urllib.parse
import graphene

from django.conf import settings
from graphene_django import DjangoObjectType
from wagtail.images.models import (
    Image as WagtailImage,
    Rendition as WagtailImageRendition,
)

from ..registry import registry
from ..utils import resolve_queryset
from .structures import QuerySetList


def get_image_url(cls):
    if hasattr(cls, 'url'):
        return cls.url

    return cls.file.url

class BaseImageObjectType(graphene.ObjectType):
    src = graphene.String()
    aspect_ratio = graphene.Float()
    sizes = graphene.String()

    def resolve_src(self, info):
        """
        Get url of the original uploaded image.
        """
        url = get_image_url(self)

        if (url[0] == '/'):
            return settings.BASE_URL + url
        return url

    def resolve_aspect_ratio(self, info, **kwargs):
        """
        Calculate aspect ratio for the image.
        """
        return self.width / self.height

    def resolve_sizes(self, info):
        return "(max-width: {}px) 100vw, {}px".format(self.width, self.width)


class ImageRenditionObjectType(DjangoObjectType, BaseImageObjectType):
    id = graphene.ID()
    url = graphene.String()
    width = graphene.Int()
    height = graphene.Int()

    class Meta:
        model = WagtailImageRendition

    def resolve_image(self, info, **kwargs):
        return self.image


class ImageObjectType(DjangoObjectType, BaseImageObjectType):
    rendition = graphene.Field(
        ImageRenditionObjectType,
        max=graphene.String(),
        min=graphene.String(),
        width=graphene.Int(),
        height=graphene.Int(),
        fill=graphene.String(),
        format=graphene.String(),
        bgcolor=graphene.String(),
        jpegquality=graphene.Int(),
    )
    src_set = graphene.String(sizes=graphene.List(graphene.Int))


    class Meta:
        model = WagtailImage
        exclude_fields = ("tags",)

    def resolve_rendition(self, info, **kwargs):
        """
        Render a custom rendition of the current image.
        """
        filters = "|".join([f"{key}-{val}" for key, val in kwargs.items()])
        img = self.get_rendition(filters)

        return ImageRenditionObjectType(
            id=img.id, 
            url=img.url, 
            width=img.width, 
            height=img.height,
            file=img.file,
            image=self
        )

    def resolve_src_set(self, info, sizes, **kwargs):
        """
        Generate src set of renditions.
        """
        rendition_list = [
            ImageObjectType.resolve_rendition(self, info, width=width)
            for width in sizes
        ]

        return ", ".join(
            [f"{settings.BASE_URL + img.url} {img.width}w" for img in rendition_list]
        )

def ImagesQuery():
    from wagtail.images import get_image_model

    registry.images[WagtailImage] = ImageObjectType
    mdl = get_image_model()
    model_type = registry.images[mdl]

    class Mixin:
        images = QuerySetList(model_type, enable_search=True)

        # Return all pages, ideally specific.
        def resolve_images(self, info, **kwargs):
            return resolve_queryset(mdl.objects.all(), info, **kwargs)

    return Mixin

def get_image_type():
    from wagtail.images import get_image_model

    registry.images[WagtailImage] = ImageObjectType
    mdl = get_image_model()
    return registry.images[mdl]
