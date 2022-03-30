import graphene
from django.utils.text import slugify
from wagtail.core import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

from grapple.helpers import register_streamfield_block
from grapple.models import (
    GraphQLCollection,
    GraphQLEmbed,
    GraphQLField,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLStreamfield,
    GraphQLString,
)


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
    mainbutton = ButtonBlock()

    graphql_fields = [
        GraphQLString("text"),
        GraphQLImage("image"),
        GraphQLStreamfield("buttons"),
        GraphQLStreamfield(
            "mainbutton", is_list=False
        ),  # this is a direct StructBlock, not a list of sub-blocks
    ]


@register_streamfield_block
class TextWithCallableBlock(blocks.StructBlock):
    text = blocks.CharBlock()

    graphql_fields = [
        GraphQLString("text"),
        GraphQLString("simple_string"),
        GraphQLString("simple_string_method", source="get_simple_string_method"),
        GraphQLField("field_property", graphene.String, source="get_field_property"),
        GraphQLField("field_method", graphene.String, source="get_field_method"),
    ]

    @property
    def simple_string(self):
        return "A simple string property."

    def simple_string_method(self, values):
        # Should not be used as we define `source="get_simple_string_method"`.
        raise Exception

    def get_simple_string_method(self, values):
        return slugify(values.get("text"))

    @property
    def get_field_property(self):
        return "A field property."

    def get_field_method(self, values):
        return slugify(values.get("text"))


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
    page = blocks.PageChooserBlock()
    text_with_callable = TextWithCallableBlock()
