from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from grapple.helpers import register_streamfield_block
from grapple.models import (
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLString,
    GraphQLCollection,
    GraphQLEmbed,
    GraphQLStreamfield,
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


@register_streamfield_block
class CarouselBlock(blocks.StreamBlock):
    text = blocks.CharBlock(classname="full title")
    image = ImageChooserBlock()
    markup = blocks.RichTextBlock()


@register_streamfield_block
class CalloutBlock(blocks.StructBlock):
    text = blocks.RichTextBlock()
    image = ImageChooserBlock()

    graphql_fields = [GraphQLString("text"), GraphQLImage("image")]


@register_streamfield_block
class ButtonBlock(blocks.StructBlock):
    button_text = blocks.CharBlock(required=True, max_length=50, label="Text")
    button_link = blocks.CharBlock(required=True, max_length=255, label="Link")

    graphql_fields = [GraphQLString("button_text"), GraphQLString("button_link")]


@register_streamfield_block
class TextAndButtonsBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    buttons = blocks.ListBlock(ButtonBlock())

    graphql_fields = [
        GraphQLString("text"),
        GraphQLImage("image"),
        GraphQLStreamfield("buttons"),
    ]


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
    carousel = CarouselBlock()
    callout = CalloutBlock()
    text_and_buttons = TextAndButtonsBlock()
