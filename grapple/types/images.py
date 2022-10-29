import graphene
from graphene_django import DjangoObjectType
from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.images import get_image_model
from wagtail.images.models import Image as WagtailImage
from wagtail.images.models import Rendition as WagtailImageRendition
from wagtail.images.models import SourceImageIOError

from ..registry import registry
from ..settings import grapple_settings
from ..utils import get_media_item_url, resolve_queryset
from .collections import CollectionObjectType
from .structures import QuerySetList
from .tags import TagObjectType


class BaseImageObjectType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    file = graphene.String(required=True)
    width = graphene.Int(required=True)
    height = graphene.Int(required=True)
    created_at = graphene.DateTime(required=True)
    focal_point_x = graphene.Int()
    focal_point_y = graphene.Int()
    focal_point_width = graphene.Int()
    focal_point_height = graphene.Int()
    file_size = graphene.Int()
    file_hash = graphene.String(required=True)
    src = graphene.String(required=True, deprecation_reason="Use the `url` attribute")
    url = graphene.String(required=True)
    aspect_ratio = graphene.Float(required=True)
    sizes = graphene.String(required=True)
    collection = graphene.Field(lambda: CollectionObjectType, required=True)
    tags = graphene.List(graphene.NonNull(lambda: TagObjectType), required=True)

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

    def resolve_tags(self, info, **kwargs):
        return self.tags.all()


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
    allowed_filters = grapple_settings.ALLOWED_IMAGE_FILTERS
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
    src_set = graphene.String(
        sizes=graphene.List(graphene.Int), format=graphene.String()
    )

    class Meta:
        model = WagtailImage

    def resolve_rendition(self, info, **kwargs):
        """
        Render a custom rendition of the current image.
        """
        filters = "|".join([f"{key}-{val}" for key, val in kwargs.items()])

        # Only allowed the defined filters (thus renditions)
        if rendition_allowed(filters):
            try:
                img = self.get_rendition(filters)
            except SourceImageIOError:
                return

            rendition_type = get_rendition_type()

            return rendition_type(
                id=img.id,
                url=get_media_item_url(img),
                width=img.width,
                height=img.height,
                file=img.file,
                image=self,
            )

    def resolve_src_set(self, info, sizes, format=None, **kwargs):
        """
        Generate src set of renditions.
        """
        filter_suffix = f"|format-{format}" if format else ""
        format_kwarg = {"format": format} if format else {}
        if self.file.name is not None:
            rendition_list = [
                ImageObjectType.resolve_rendition(
                    self, info, width=width, **format_kwarg
                )
                for width in sizes
                if rendition_allowed(f"width-{width}{filter_suffix}")
            ]

            return ", ".join(
                [
                    f"{get_media_item_url(img)} {img.width}w"
                    for img in rendition_list
                    if img is not None
                ]
            )

        return ""


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
                qs = mdl.objects.filter(collection__view_restrictions__isnull=True)
                if WAGTAIL_VERSION >= (3, 0):
                    qs = qs.prefetch_related("renditions")
                return qs.get(pk=id)
            except mdl.DoesNotExist:
                return None

        def resolve_images(self, info, **kwargs):
            """Returns all images in a public collection"""
            qs = mdl.objects.filter(collection__view_restrictions__isnull=True)
            if WAGTAIL_VERSION >= (4, 0):
                qs = qs.prefetch_renditions()
            elif WAGTAIL_VERSION >= (3, 0):
                qs = qs.prefetch_related("renditions")

            return resolve_queryset(qs, info, **kwargs)

        # Give name of the image type, used to generate mixins
        def resolve_image_type(self, info, **kwargs):
            return get_image_type()

    return Mixin
