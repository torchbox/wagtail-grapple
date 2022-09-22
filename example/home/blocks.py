from typing import Any, Dict, Optional

import graphene
from django.utils.text import slugify
from wagtail.core import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from grapple.helpers import register_streamfield_block
from grapple.models import (
    GraphQLBoolean,
    GraphQLCollection,
    GraphQLEmbed,
    GraphQLField,
    GraphQLFloat,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLInt,
    GraphQLRichText,
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

    graphql_fields = [GraphQLRichText("text"), GraphQLImage("image")]


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
class BlockWithName(blocks.StructBlock):
    """
    wagtail.core.blocks.Block defines a name property inherited by all blocks.
    Ensure that when we bind a block to "name" that the block's value is
    returned in GraphQL queries.
    """

    name = blocks.TextBlock()

    graphql_fields = [
        GraphQLString("name"),
    ]


@register_streamfield_block
class TextWithCallableBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    integer = blocks.IntegerBlock()
    decimal = blocks.FloatBlock()

    graphql_fields = [
        GraphQLString("text"),
        GraphQLInt("integer"),
        GraphQLFloat("decimal"),
        # GraphQLString test attributes
        GraphQLString("simple_string"),
        GraphQLString("simple_string_method", source="get_simple_string_method"),
        # GraphQLInt test attributes
        GraphQLInt("simple_int"),
        GraphQLInt("simple_int_method", source="get_simple_int_method"),
        # GraphQLFloat test attributes
        GraphQLFloat("simple_float"),
        GraphQLFloat("simple_float_method", source="get_simple_float_method"),
        # GraphQLBoolean test attributes
        GraphQLBoolean("simple_boolean"),
        GraphQLBoolean("simple_boolean_method", source="get_simple_boolean_method"),
        # GraphQLField test attributes
        GraphQLField("field_property", graphene.String, source="get_field_property"),
        GraphQLField("field_method", graphene.String, source="get_field_method"),
    ]

    # GraphQLString test attributes

    @property
    def simple_string(self) -> str:
        return "A simple string property."

    def simple_string_method(
        self,
        values: Dict[str, Any] = None,
    ):
        # Should not be used as we define `source="get_simple_string_method"`.
        raise Exception

    def get_simple_string_method(
        self,
        values: Dict[str, Any] = None,
    ) -> Optional[str]:
        return slugify(values.get("text")) if values else None

    # GraphQLInt test attributes

    @property
    def simple_int(self) -> int:
        return 5

    def simple_int_method(
        self,
        values: Dict[str, Any] = None,
    ):
        # Should not be used as we define `source="get_simple_int_method"`.
        raise Exception

    def get_simple_int_method(
        self,
        values: Dict[str, Any] = None,
    ) -> Optional[int]:
        return values.get("integer") * 2 if values else None

    # GraphQLFloat test attributes

    @property
    def simple_float(self) -> float:
        return 0.1

    def simple_float_method(
        self,
        values: Dict[str, Any] = None,
    ):
        # Should not be used as we define `source="get_simple_float_method"`.
        raise Exception

    def get_simple_float_method(
        self,
        values: Dict[str, Any] = None,
    ) -> Optional[float]:
        return values.get("decimal") * 2 if values else None

    # GraphQLBoolean test attributes

    @property
    def simple_boolean(self) -> bool:
        return 1

    def simple_boolean_method(
        self,
        values: Dict[str, Any] = None,
    ):
        # Should not be used as we define `source="get_simple_boolean_method"`.
        raise Exception

    def get_simple_boolean_method(
        self,
        values: Dict[str, Any] = None,
    ) -> Optional[bool]:
        return bool(values.get("text")) if values else None

    # GraphQLField test attributes

    @property
    def get_field_property(self) -> str:
        return "A field property."

    def field_method(
        self,
        values: Dict[str, Any] = None,
    ):
        # Should not be used as we define `source="get_field_method"`.
        raise Exception

    def get_field_method(
        self,
        values: Dict[str, Any] = None,
    ) -> Optional[str]:
        return slugify(values.get("text")) if values else None


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
    block_with_name = BlockWithName()
    advert = SnippetChooserBlock("home.Advert")
    person = SnippetChooserBlock("home.Person")
