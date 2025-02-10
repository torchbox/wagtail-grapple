from typing import Optional

import graphene

# TODO: use specific imports
import wagtail
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks

from graphene.types import Scalar
from graphene_django.converter import convert_django_field
from wagtail import blocks
from wagtail.embeds.blocks import EmbedValue
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.exceptions import EmbedException
from wagtail.fields import StreamField

from ..registry import registry
from .interfaces import StreamFieldInterface
from .rich_text import RichText as RichTextType


class GenericStreamFieldInterface(Scalar):
    @staticmethod
    def serialize(stream_value):
        try:
            return stream_value.raw_data
        except AttributeError:
            return stream_value.stream_data


@convert_django_field.register(StreamField)
def convert_stream_field(field, registry=None):
    return GenericStreamFieldInterface(
        description=field.help_text, required=not field.null
    )


def generate_streamfield_union(graphql_types):
    class StreamfieldUnion(graphene.Union):
        class Meta:
            types = graphql_types

        @classmethod
        def resolve_type(cls, instance, info):
            """
            If block has a custom Graphene Node type in registry then use it,
            otherwise use generic block type.
            """
            mdl = type(instance.block)
            if mdl in registry.streamfield_blocks:
                return registry.streamfield_blocks[mdl]

            return registry.streamfield_blocks["generic-block"]

    return StreamfieldUnion


class StructBlockItem:
    id = None
    block = None
    value = None

    def __init__(self, id, block, value=""):
        self.id = id
        self.block = block
        self.value = value


class StructBlock(graphene.ObjectType):
    class Meta:
        interfaces = (StreamFieldInterface,)

    blocks = graphene.List(graphene.NonNull(StreamFieldInterface), required=True)

    def resolve_blocks(self, info, **kwargs):
        stream_blocks = []

        if issubclass(type(self.value), blocks.stream_block.StreamValue):
            # self: StreamChild, block: StreamBlock, value: StreamValue
            stream_data = self.value[0]
            child_blocks = self.value.stream_block.child_blocks
        else:
            # This occurs when StreamBlock is child of StructBlock
            # self: StructBlockItem, block: StreamBlock, value: list
            stream_data = self.value
            child_blocks = self.block.child_blocks

        for field, value in stream_data.items():
            block = dict(child_blocks)[field]
            if isinstance(value, int) and (
                issubclass(type(block), blocks.ChooserBlock)
                or not issubclass(type(block), blocks.StructBlock)
            ):
                value = block.to_python(value)

            stream_blocks.append(StructBlockItem(field, block, value))

        return stream_blocks


class StreamBlock(StructBlock):
    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_blocks(self, info, **kwargs):
        child_blocks = self.value.stream_block.child_blocks

        return [
            StructBlockItem(
                id=stream.id, block=child_blocks[stream.block_type], value=stream.value
            )
            for stream in self.value
        ]


class StreamFieldBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class CharBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class TextBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class EmailBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class IntegerBlock(graphene.ObjectType):
    value = graphene.Int(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class FloatBlock(graphene.ObjectType):
    value = graphene.Float(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class DecimalBlock(graphene.ObjectType):
    value = graphene.Float(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class RegexBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class URLBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class BooleanBlock(graphene.ObjectType):
    value = graphene.Boolean(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class DateBlock(graphene.ObjectType):
    value = graphene.String(format=graphene.String(), required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_value(self, info, **kwargs):
        format = kwargs.get("format")
        if format:
            return self.value.strftime(format)
        return self.value


class DateTimeBlock(DateBlock):
    class Meta:
        interfaces = (StreamFieldInterface,)


class TimeBlock(DateBlock):
    class Meta:
        interfaces = (StreamFieldInterface,)


class RichTextBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_value(self, info, **kwargs):
        return RichTextType.serialize(self.value.source)


class RawHTMLBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class BlockQuoteBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class ChoiceOption(graphene.ObjectType):
    key = graphene.String(required=True)
    value = graphene.String(required=True)


class ChoiceBlock(graphene.ObjectType):
    value = graphene.String(required=True)
    choices = graphene.List(graphene.NonNull(ChoiceOption), required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_choices(self, info, **kwargs):
        choices = []
        for key, value in self.block._constructor_kwargs["choices"]:
            choice = ChoiceOption(key, value)
            choices.append(choice)
        return choices


def get_embed_url(instance):
    return instance.value.url if hasattr(instance, "value") else instance.url


def get_embed_object(instance):
    try:
        return get_embed(get_embed_url(instance))
    except EmbedException:
        pass


class EmbedBlock(graphene.ObjectType):
    value = graphene.String(required=True)
    url = graphene.String(required=True)
    embed = graphene.String()
    raw_embed = graphene.JSONString()

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_url(self: EmbedValue, info, **kwargs) -> str:
        return get_embed_url(self)

    def resolve_raw_value(self: EmbedValue, info, **kwargs) -> str:
        if isinstance(self, EmbedValue):
            return self
        return StreamFieldInterface.resolve_raw_value(info, **kwargs)

    def resolve_value(self: EmbedValue, info, **kwargs) -> str:
        return EmbedBlock.resolve_raw_value(self, info, **kwargs)

    def resolve_embed(self: EmbedValue, info, **kwargs) -> Optional[str]:
        embed = get_embed_object(self)
        if embed:
            return embed.html

    def resolve_raw_embed(self: EmbedValue, info, **kwargs) -> Optional[str]:
        embed = get_embed_object(self)
        if embed:
            return {
                "title": embed.title,
                "type": embed.type,
                "thumbnail_url": embed.thumbnail_url,
                "width": embed.width,
                "height": embed.height,
                "html": embed.html,
            }


class StaticBlock(graphene.ObjectType):
    value = graphene.String(required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)


class ListBlock(graphene.ObjectType):
    items = graphene.List(graphene.NonNull(StreamFieldInterface), required=True)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_items(self, info, **kwargs):
        # Get the nested StreamBlock type
        block_type = self.block.child_block
        # Return a list of GraphQL types from the list of values
        return [StructBlockItem(self.id, block_type, item) for item in self.value]


registry.streamfield_blocks.update(
    {
        "generic-block": StreamFieldBlock,
        blocks.CharBlock: CharBlock,
        blocks.TextBlock: TextBlock,
        blocks.EmailBlock: EmailBlock,
        blocks.IntegerBlock: IntegerBlock,
        blocks.FloatBlock: FloatBlock,
        blocks.DecimalBlock: DecimalBlock,
        blocks.RegexBlock: RegexBlock,
        blocks.URLBlock: URLBlock,
        blocks.BooleanBlock: BooleanBlock,
        blocks.DateBlock: DateBlock,
        blocks.TimeBlock: TimeBlock,
        blocks.DateTimeBlock: DateTimeBlock,
        blocks.RichTextBlock: RichTextBlock,
        blocks.RawHTMLBlock: RawHTMLBlock,
        blocks.BlockQuoteBlock: BlockQuoteBlock,
        blocks.ChoiceBlock: ChoiceBlock,
        blocks.StreamBlock: StreamBlock,
        blocks.StructBlock: StructBlock,
        blocks.StaticBlock: StaticBlock,
        blocks.ListBlock: ListBlock,
        wagtail.embeds.blocks.EmbedBlock: EmbedBlock,
    }
)


def register_streamfield_blocks():
    from .documents import get_document_type
    from .images import get_image_type
    from .interfaces import get_page_interface, get_snippet_interface

    class PageChooserBlock(graphene.ObjectType):
        page = graphene.Field(get_page_interface(), required=False)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_page(self, info, **kwargs):
            return self.value.specific

    class DocumentChooserBlock(graphene.ObjectType):
        document = graphene.Field(get_document_type(), required=False)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_document(self, info, **kwargs):
            return self.value

    class ImageChooserBlock(graphene.ObjectType):
        image = graphene.Field(get_image_type(), required=False)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_image(self, info, **kwargs):
            return self.value

    class ImageBlock(graphene.ObjectType):
        image = graphene.Field(get_image_type, required=False)
        decorative = graphene.Boolean(required=False)
        alt_text = graphene.String(required=False)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_image(self, info, **kwargs):
            return self.value

        def resolve_decorative(self, info, **kwargs):
            return self.value.decorative

        def resolve_alt_text(self, info, **kwargs):
            return self.value.contextual_alt_text

    registry.streamfield_blocks.update(
        {
            blocks.PageChooserBlock: PageChooserBlock,
            wagtail.documents.blocks.DocumentChooserBlock: DocumentChooserBlock,
            wagtail.images.blocks.ImageChooserBlock: ImageChooserBlock,
            wagtail.images.blocks.ImageBlock: ImageBlock,
        }
    )

    class SnippetChooserBlock(graphene.ObjectType):
        snippet = graphene.Field(get_snippet_interface(), required=False)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_snippet(self, info, **kwargs):
            return self.value

    registry.streamfield_blocks.update(
        {
            wagtail.snippets.blocks.SnippetChooserBlock: SnippetChooserBlock,
        }
    )
