from __future__ import annotations

from typing import TYPE_CHECKING

import graphene

from graphene_django import DjangoObjectType
from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.images import get_image_model
from wagtail.images.models import Image as WagtailImage
from wagtail.images.models import Rendition as WagtailImageRendition

from ..registry import registry
from ..settings import grapple_settings
from ..utils import get_media_item_url, resolve_queryset
from .collections import CollectionObjectType
from .structures import QuerySetList
from .tags import TagObjectType


if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

if WAGTAIL_VERSION > (5, 0):
    from wagtail.images.utils import to_svg_safe_spec


def get_image_type():
    return registry.images.get(get_image_model(), ImageObjectType)


def get_rendition_type():
    rendition_mdl = get_image_model().renditions.rel.related_model
    return registry.images.get(rendition_mdl, ImageRenditionObjectType)


def get_rendition_field_kwargs() -> dict[str, graphene.Scalar]:
    """
    Returns a list of kwargs for the rendition field.
    Extracted for convenience, to accommodate for the conditional logic needed for various Wagtail versions.
    """
    kwargs = {
        "max": graphene.String(),
        "min": graphene.String(),
        "width": graphene.Int(),
        "height": graphene.Int(),
        "fill": graphene.String(),
        "format": graphene.String(),
        "bgcolor": graphene.String(),
        "jpegquality": graphene.Int(),
        "webpquality": graphene.Int(),
    }
    if WAGTAIL_VERSION > (5, 0):
        kwargs["preserve_svg"] = graphene.Boolean(
            description="Prevents raster image operations (e.g. `format-webp`, `bgcolor`, etc.) being applied to SVGs. "
            "More info: https://docs.wagtail.org/en/stable/topics/images.html#svg-images"
        )

    return kwargs


def rendition_allowed(filter_specs: str) -> bool:
    """Checks a given rendition filter is allowed"""
    allowed_filters = grapple_settings.ALLOWED_IMAGE_FILTERS
    if allowed_filters is None or not isinstance(allowed_filters, (list, tuple)):
        return True

    return filter_specs in allowed_filters


class ImageRenditionObjectType(DjangoObjectType):
    id = graphene.ID(required=True)
    file = graphene.String(required=True)
    image = graphene.Field(lambda: get_image_type(), required=True)
    filter_spec = graphene.String(required=True)
    width = graphene.Int(required=True)
    height = graphene.Int(required=True)
    focal_point_key = graphene.String(required=True)
    focal_point = graphene.String()
    url = graphene.String(required=True)
    alt = graphene.String(required=True)
    background_position_style = graphene.String(required=True)

    class Meta:
        model = WagtailImageRendition

    def resolve_url(
        instance: WagtailImageRendition, info: GraphQLResolveInfo, **kwargs
    ):
        return instance.full_url


class ImageObjectType(DjangoObjectType):
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
    rendition = graphene.Field(get_rendition_type, **get_rendition_field_kwargs())
    src_set = graphene.String(
        sizes=graphene.List(graphene.Int), format=graphene.String()
    )
    if WAGTAIL_VERSION > (5, 0):
        is_svg = graphene.Boolean(required=True)

    class Meta:
        model = WagtailImage

    def resolve_rendition(
        instance: WagtailImage, info: GraphQLResolveInfo, **kwargs
    ) -> WagtailImageRendition | None:
        """
        Render a custom rendition of the current image.
        """
        preserve_svg = kwargs.pop("preserve_svg", False)
        filter_specs = "|".join([f"{key}-{val}" for key, val in kwargs.items()])

        # Only allow the defined filters (thus renditions)
        if not rendition_allowed(filter_specs):
            raise TypeError(
                "Invalid filter specs. Check the `ALLOWED_IMAGE_FILTERS` setting."
            )

        if instance.is_svg() and preserve_svg:
            # when dealing with SVGs, we want to limit the filter specs to those that are safe
            filter_specs = to_svg_safe_spec(filter_specs)

            if not filter_specs:
                raise TypeError(
                    "No valid filter specs for SVG. "
                    "See https://docs.wagtail.org/en/stable/topics/images.html#svg-images for details."
                )

        # previously we wrapped this in a try/except SourceImageIOError block.
        # Removed to allow the error to bubble up in the response ("errors") and be handled by the user.
        return instance.get_rendition(filter_specs)

    def resolve_url(instance: WagtailImage, info: GraphQLResolveInfo, **kwargs) -> str:
        """
        Get the uploaded image url.
        """
        return get_media_item_url(instance)

    def resolve_src(self: WagtailImage, info, **kwargs) -> str:
        """
        Deprecated. Use the `url` attribute.
        """
        return get_media_item_url(self)

    def resolve_aspect_ratio(
        instance: WagtailImage, info: GraphQLResolveInfo, **kwargs
    ):
        """
        Calculate aspect ratio for the image.
        """
        return instance.width / instance.height

    def resolve_sizes(
        instance: WagtailImage, info: GraphQLResolveInfo, **kwargs
    ) -> str:
        return f"(max-width: {instance.width}px) 100vw, {instance.width}px"

    def resolve_tags(instance: WagtailImage, info: GraphQLResolveInfo, **kwargs):
        return instance.tags.all()

    def resolve_src_set(
        instance: WagtailImage,
        info: GraphQLResolveInfo,
        sizes: list[int],
        format: str | None = None,
        **kwargs,
    ) -> str:
        """
        Generate src set of renditions.
        """
        filter_suffix = f"|format-{format}" if format else ""
        format_kwarg = {"format": format} if format else {}
        if instance.file.name is not None:
            rendition_list = [
                ImageObjectType.resolve_rendition(
                    instance, info, width=width, **format_kwarg
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

    if WAGTAIL_VERSION > (5, 0):

        def resolve_is_svg(
            instance: WagtailImage, info: GraphQLResolveInfo, **kwargs
        ) -> bool:
            return instance.is_svg()


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

        def resolve_image(parent, info, id, **kwargs):
            """Returns an image given the id, if in a public collection"""
            try:
                return (
                    mdl.objects.filter(collection__view_restrictions__isnull=True)
                    .prefetch_renditions()
                    .get(pk=id)
                )
            except mdl.DoesNotExist:
                return None

        def resolve_images(parent, info, **kwargs):
            """Returns all images in a public collection"""
            return resolve_queryset(
                mdl.objects.filter(
                    collection__view_restrictions__isnull=True
                ).prefetch_renditions(),
                info,
                **kwargs,
            )

        # Give name of the image type, used to generate mixins
        def resolve_image_type(parent, info, **kwargs):
            return mdl_type

    return Mixin
