from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from grapple.helpers import register_streamfield_block
from grapple.models import (
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLString,
    GraphQLCollection,
    GraphQLEmbed,
)

from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock


@register_streamfield_block
class ImageGalleryImage(blocks.StructBlock):
    caption = blocks.CharBlock(classname="full title")
    image = ImageChooserBlock()

    graphql_fields = [GraphQLString("caption"), GraphQLImage("image")]


@register_streamfield_block
class ImageGalleryImages(blocks.StreamBlock):
    image = ImageGalleryImage()

    child_blocks = {"image": ImageGalleryImage}

    class Meta:
        min_num = 2
        max_num = 15


@register_streamfield_block
class ImageGalleryBlock(blocks.StructBlock):
    title = blocks.CharBlock(classname="full title")
    images = ImageGalleryImages()

    graphql_fields = [
        GraphQLString("title"),
        GraphQLCollection(GraphQLForeignKey, "images", ImageGalleryImage),
    ]


@register_streamfield_block
class VideoBlock(blocks.StructBlock):
    youtube_link = EmbedBlock(required=False)

    graphql_fields = [GraphQLEmbed("youtube_link")]


class StreamFieldBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(classname="full title")
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()
    decimal = blocks.DecimalBlock()
    date = blocks.DateBlock()
    datetime = blocks.DateTimeBlock()
    gallery = ImageGalleryBlock()
    video = VideoBlock()
    objectives = blocks.ListBlock(blocks.CharBlock())
