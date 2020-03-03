import json
import graphene
import wagtail
import inspect
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks
from django.conf import settings
from graphene.types import Scalar
from graphene_django.converter import convert_django_field
from wagtail.core.fields import StreamField
from wagtail.core import blocks

from ..registry import registry


class GenericStreamFieldInterface(Scalar):
    @staticmethod
    def serialize(stream_value):
        return stream_value.stream_data


@convert_django_field.register(StreamField)
def convert_stream_field(field, registry=None):
    return GenericStreamFieldInterface(
        description=field.help_text, required=not field.null
    )


class StreamFieldInterface(graphene.Interface):
    id = graphene.String()
    block_type = graphene.String()
    field = graphene.String()
    raw_value = graphene.String()

    @classmethod
    def resolve_type(cls, instance, info):
        """
        If block has a custom Graphene Node type in registry then use it,
        otherwise use generic block type.
        """
        if hasattr(instance, "block"):
            mdl = type(instance.block)
            if mdl in registry.streamfield_blocks:
                return registry.streamfield_blocks[mdl]

            for block_class in inspect.getmro(mdl):
                if block_class in registry.streamfield_blocks:
                    return registry.streamfield_blocks[block_class]

        return registry.streamfield_blocks["generic-block"]

    def resolve_id(self, info, **kwargs):
        return self.id

    def resolve_block_type(self, info, **kwargs):
        return type(self.block).__name__

    def resolve_field(self, info, **kwargs):
        return self.block.name

    def resolve_raw_value(self, info, **kwargs):
        if isinstance(self.value, dict):
            return serialize_struct_obj(self.value)

        return self.value


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


def serialize_struct_obj(obj):
    rtn_obj = {}

    if hasattr(obj, "stream_data"):
        rtn_obj = []
        for field in obj.stream_data:
            rtn_obj.append(serialize_struct_obj(field["value"]))
    else:
        for field in obj:
            value = obj[field]
            if hasattr(value, "stream_data"):
                rtn_obj[field] = list(
                    map(
                        lambda data: serialize_struct_obj(data["value"]),
                        value.stream_data,
                    )
                )
            elif hasattr(value, "value"):
                rtn_obj[field] = value.value
            elif hasattr(value, "src"):
                rtn_obj[field] = value.src
            elif hasattr(value, "file"):
                rtn_obj[field] = value.file.url
            else:
                rtn_obj[field] = value

    return rtn_obj


class StructBlock(graphene.ObjectType):
    class Meta:
        interfaces = (StreamFieldInterface,)

    blocks = graphene.List(StreamFieldInterface)

    def resolve_blocks(self, info, **kwargs):
        stream_blocks = []
        for name, value in self.value.items():
            block = self.block.child_blocks[name]
            if not issubclass(type(block), blocks.StreamBlock):
                value = block.to_python(value)

            stream_blocks.append(StructBlockItem(name, block, value))
        return stream_blocks


class StreamBlock(StructBlock):
    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_blocks(self, info, **kwargs):
        stream_blocks = []
        for field in self.value.stream_data:
            block = self.value.stream_block.child_blocks[field["type"]]
            if not issubclass(type(block), blocks.StructBlock):
                value = block.to_python(field["value"])

            stream_blocks.append(StructBlockItem(field["type"], block, field["value"]))
        return stream_blocks


class StreamFieldBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class CharBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class TextBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class EmailBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class IntegerBlock(graphene.ObjectType):
    value = graphene.Int()

    class Meta:
        interfaces = (StreamFieldInterface,)


class FloatBlock(graphene.ObjectType):
    value = graphene.Float()

    class Meta:
        interfaces = (StreamFieldInterface,)


class DecimalBlock(graphene.ObjectType):
    value = graphene.Float()

    class Meta:
        interfaces = (StreamFieldInterface,)


class RegexBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class URLBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class BooleanBlock(graphene.ObjectType):
    value = graphene.Boolean()

    class Meta:
        interfaces = (StreamFieldInterface,)


class DateBlock(graphene.ObjectType):
    value = graphene.String(format=graphene.String())

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
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class RawHTMLBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class BlockQuoteBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class ChoiceOption(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class ChoiceBlock(graphene.ObjectType):
    value = graphene.String()
    choices = graphene.List(ChoiceOption)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_choices(self, info, **kwargs):
        choices = []
        for key, value in self.block._constructor_kwargs["choices"]:
            choice = ChoiceOption(key, value)
            choices.append(choice)
        return choices


def get_media_url(url):
    if url[0] == "/":
        return settings.BASE_URL + url
    return url


class EmbedBlock(graphene.ObjectType):
    value = graphene.String()
    url = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_url(self, info, **kwargs):
        if hasattr(self, "value"):
            return get_media_url(self.value.url)
        return get_media_url(self.url)


class StaticBlock(graphene.ObjectType):
    value = graphene.String()

    class Meta:
        interfaces = (StreamFieldInterface,)


class ListBlock(graphene.ObjectType):
    items = graphene.List(StreamFieldInterface)

    class Meta:
        interfaces = (StreamFieldInterface,)

    def resolve_items(self, info, **kwargs):
        # Get the nested StreamBlock type
        block_type = self.block.child_block
        # Return a list of GraphQL types from the list of valuess
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
    from .pages import PageInterface
    from .documents import get_document_type
    from .images import get_image_type

    class PageChooserBlock(graphene.ObjectType):
        page = graphene.Field(PageInterface)

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_page(self, info, **kwargs):
            return self.value

    class DocumentChooserBlock(graphene.ObjectType):
        document = graphene.Field(get_document_type())

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_document(self, info, **kwargs):
            return self.value

    class ImageChooserBlock(graphene.ObjectType):
        image = graphene.Field(get_image_type())

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_image(self, info, **kwargs):
            return self.value

    class SnippetChooserBlock(graphene.ObjectType):
        snippet = graphene.String()

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_snippet(self, info, **kwargs):
            return self.value

    registry.streamfield_blocks.update(
        {
            blocks.PageChooserBlock: PageChooserBlock,
            wagtail.documents.blocks.DocumentChooserBlock: DocumentChooserBlock,
            wagtail.images.blocks.ImageChooserBlock: ImageChooserBlock,
            wagtail.snippets.blocks.SnippetChooserBlock: SnippetChooserBlock,
        }
    )
