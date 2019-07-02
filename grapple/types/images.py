import os
import urllib.parse
import graphene

from django.conf import settings
from graphene_django import DjangoObjectType
from wagtail.images.models import (
    Image as WagtailImage,
    Rendition as WagtailImageRendition,
)

from ..registry import registry
from ..utils import (
    convert_image_to_bmp,
    trace_bitmap,
    image_as_base64,
    resolve_queryset,
)
from .structures import QuerySetList


class ImageRenditionObjectType(DjangoObjectType):
    id = graphene.ID()
    url = graphene.String()
    width = graphene.Int()
    height = graphene.Int()

    class Meta:
        model = WagtailImageRendition


class ImageObjectType(DjangoObjectType):
    src = graphene.String()
    src_set = graphene.String(sizes=graphene.List(graphene.Int))
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
    traced_SVG = graphene.String(name='tracedSVG')
    base64 = graphene.String()
    aspect_ratio = graphene.Float()
    sizes = graphene.String()

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
            id=img.id, url=img.url, width=img.width, height=img.height
        )

    def resolve_src(self, info):
        """
        Get url of the original uploaded image.
        """
        return settings.BASE_URL + self.file.url

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

    def resolve_base64(self, info):
        """
        Intended to be used by Gatsby Image. Return the image as base-encoded string so that it can be pre-rendered
        as background image while actual image is downloaded via network.
        """
        return image_as_base64(self.file.url)

    def resolve_traced_SVG(self, info):
        """
        Intended to be used by Gatsby Image. Trace a bitmap image and return a small-sized svg that can be pre-rendered
        as background image while actual image is downloaded via network.
        """
        temp_image = convert_image_to_bmp(settings.BASE_DIR + self.file.url)
        svg_trace_image = (
            settings.BASE_DIR + os.path.splitext(self.file.url)[0] + "-traced.svg"
        )
        if not os.path.isfile(svg_trace_image):
            trace_bitmap(temp_image, svg_trace_image)

        with open(svg_trace_image, "r") as svgFile:
            return "data:image/svg+xml," + urllib.parse.quote(svgFile.read())

    def resolve_aspect_ratio(self, info, **kwargs):
        """
        Calculate aspect ratio for Gatsby Image.
        """
        return self.width / self.height

    def resolve_sizes(self, info):
        return "(max-width: {}px) 100vw, {}px".format(self.width, self.width)


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
