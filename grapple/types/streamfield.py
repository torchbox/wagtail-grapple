import graphene
import wagtail
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks
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
    return GenericStreamFieldInterface(description=field.help_text, required=not field.null)


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
        mdl = type(instance.block)
        if mdl in registry.streamfield_blocks:
            return registry.streamfield_blocks[mdl]
        else:
            return registry.streamfield_blocks["generic-block"]

    def resolve_id(self, info, **kwargs):
        return self.id

    def resolve_block_type(self, info, **kwargs):
        return type(self.block).__name__

    def resolve_field(self, info, **kwargs):
        return self.block.name

    def resolve_raw_value(self, info, **kwargs):
        return self.value


def register_streamfield_blocks():
    from .pages import PageInterface
    from .documents import get_document_type
    from .images import get_image_type

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
            for key, value in self.block._constructor_kwargs['choices']:
                choice = ChoiceOption(key, value)
                choices.append(choice)
            return choices

    class EmbedBlock(graphene.ObjectType):
        value = graphene.String()
        url = graphene.String()

        class Meta:
            interfaces = (StreamFieldInterface,)

        def resolve_url(self, info, **kwargs):
            return self.value.url

    class StaticBlock(graphene.ObjectType):
        value = graphene.String()

        class Meta:
            interfaces = (StreamFieldInterface,)

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

    class ListBlock(graphene.ObjectType):
        class Meta:
            interfaces = (StreamFieldInterface,)

        items = graphene.Field(StreamFieldInterface)

        def resolve_items(self, info, **kwargs):
            return self

    class StructBlockItem:
        id = None
        block = None

        def __init__(self, id, block):
            self.id = id
            self.block = block

    class StreamBlock(graphene.ObjectType):
        class Meta:
            interfaces = (StreamFieldInterface,)

        items = graphene.List(StreamFieldInterface)

        def resolve_items(self, info, **kwargs):
            return [
                StructBlockItem(name, block)
                for name, block in self.block.child_blocks.items()
            ]

    class StructBlock(graphene.ObjectType):
        class Meta:
            interfaces = (StreamFieldInterface,)

        items = graphene.List(StreamFieldInterface)

        def resolve_items(self, info, **kwargs):
            return [
                StructBlockItem(name, block)
                for name, block in self.block.child_blocks.items()
            ]

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
            blocks.PageChooserBlock: PageChooserBlock,
            wagtail.documents.blocks.DocumentChooserBlock: DocumentChooserBlock,
            wagtail.images.blocks.ImageChooserBlock: ImageChooserBlock,
            wagtail.snippets.blocks.SnippetChooserBlock: SnippetChooserBlock,
            wagtail.embeds.blocks.EmbedBlock: EmbedBlock,
            blocks.StaticBlock: StaticBlock,
            blocks.ListBlock: ListBlock,
            blocks.StreamBlock: StreamBlock,
            blocks.StructBlock: StructBlock,
        }
    )
