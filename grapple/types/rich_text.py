from typing import Union

from graphene.types import String

try:
    from wagtail.rich_text import RichText as WagtailRichText
except ImportError:
    from wagtail.core.rich_text import RichText as WagtailRichText

from ..settings import grapple_settings


class RichText(String):
    @staticmethod
    def coerce_rich_text(rich_text: Union[str, WagtailRichText]):
        # When serializing a model instance, we get a str. When serializing a
        # RichTextBlock instance, its an instance of wagtail.rich_text.RichText already.
        if grapple_settings.RICHTEXT_FORMAT == "html":
            if isinstance(rich_text, str):
                return WagtailRichText(rich_text).__html__()
            return rich_text.__html__()
        elif isinstance(rich_text, str):
            return rich_text
        else:
            return rich_text.source

    serialize = coerce_rich_text
    parse_value = coerce_rich_text
