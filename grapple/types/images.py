import graphene

from django.conf import settings
from graphene_django import DjangoObjectType
from wagtail.images import get_image_model
from wagtail.images.models import (
    Image as WagtailImage,
    Rendition as WagtailImageRendition,
)

from ..registry import registry
from ..utils import resolve_queryset, get_media_item_url
from .collections import CollectionObjectType
from .structures import QuerySetList


class BaseImageObjectType(graphene.ObjectType):
    id = graphene.ID(required=True)
    width = graphene.Int(required=True)
    height = graphene.Int(required=True)
    src = graphene.String(required=True, deprecation_reason="Use the `url` attribute")
    url = graphene.String(required=True)
    aspect_ratio = graphene.Float(required=True)
    sizes = graphene.String(required=True)
    collection = graphene.Field(lambda: CollectionObjectType, required=True)

    def resolve_url(self, info, **kwargs):
        """
        Get the uploaded image url.
        """
        return get_media_item_url(self)

    def resolve_src(self, info, **kwargs):
        """
        Deprecated. Use the `url` attribute.
        """
        return get_media_item_url(self)

    def resolve_aspect_ratio(self, info, **kwargs):
        """
        Calculate aspect ratio for the image.
        """
        return self.width / self.height

    def resolve_sizes(self, info, **kwargs):
        return "(max-width: {}px) 100vw, {}px".format(self.width, self.width)


class ImageRenditionObjectType(DjangoObjectType, BaseImageObjectType):
    class Meta:
        model = WagtailImageRendition

    def resolve_image(self, info, **kwargs):
        return self.image


def get_rendition_type():
    rendition_mdl = get_image_model().renditions.rel.related_model
    rendition_type = registry.images.get(rendition_mdl, ImageRenditionObjectType)
    return rendition_type


def rendition_allowed(rendition_filter):
    """Checks a given rendition filter is allowed"""
    allowed_filters = getattr(settings, "GRAPPLE_ALLOWED_IMAGE_FILTERS", None)
    if allowed_filters is None or not isinstance(allowed_filters, (list, tuple)):
        return True

    return rendition_filter in allowed_filters


class ImageObjectType(DjangoObjectType, BaseImageObjectType):
    rendition = graphene.Field(
        lambda: get_rendition_type(),
        max=graphene.String(),
        min=graphene.String(),
        width=graphene.Int(),
        height=graphene.Int(),
        fill=graphene.String(),
        format=graphene.String(),
        bgcolor=graphene.String(),
        jpegquality=graphene.Int(),
        webpquality=graphene.Int(),
    )
    src_set = graphene.String(sizes=graphene.List(graphene.Int))

    class Meta:
        model = WagtailImage
        exclude = ("tags",)

    def resolve_rendition(self, info, **kwargs):
        """
        Render a custom rendition of the current image.
        """
        rendition = None
        try:
            filters = "|".join([f"{key}-{val}" for key, val in kwargs.items()])

            # Only allowed the defined filters (thus renditions)
            if rendition_allowed(filters):
                img = self.get_rendition(filters)
                rendition_type = get_rendition_type()

                rendition = rendition_type(
                    id=img.id,
                    url=img.url,
                    width=img.width,
                    height=img.height,
                    file=img.file,
                    image=self,
                )
        finally:
            return rendition

    def resolve_src_set(self, info, sizes, **kwargs):
        """
        Generate src set of renditions.
        """
        src_set = ""
        try:
            if self.file.name is not None:
                rendition_list = [
                    ImageObjectType.resolve_rendition(self, info, width=width)
                    for width in sizes
                    if rendition_allowed(f"width-{width}")
                ]

                src_set = ", ".join(
                    [
                        f"{get_media_item_url(img)} {img.width}w"
                        for img in rendition_list
                    ]
                )
        finally:
            return src_set


def get_image_type():
    mdl = get_image_model()
    return registry.images.get(mdl, ImageObjectType)


def ImagesQuery():
    mdl = get_image_model()
    mdl_type = get_image_type()

    class Mixin:
        image = graphene.Field(mdl_type, id=graphene.ID())
        images = QuerySetList(
            graphene.NonNull(mdl_type),
            enable_search=True,
            required=True,
            collection=graphene.Argument(
                graphene.ID, description="Filter by collection id"
            ),
        )
        image_type = graphene.String(required=True)

        def resolve_image(self, info, id, **kwargs):
            """Returns an image given the id, if in a public collection"""
            try:
                return mdl.objects.filter(
                    collection__view_restrictions__isnull=True
                ).get(pk=id)
            except BaseException:
                return None

        def resolve_images(self, info, **kwargs):
            """Returns all images in a public collection"""
            qs = mdl.objects.filter(collection__view_restrictions__isnull=True)
            return resolve_queryset(qs, info, **kwargs)

        # Give name of the image type, used to generate mixins
        def resolve_image_type(self, info, **kwargs):
            return get_image_type()

    return Mixin
