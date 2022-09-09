from graphene.types import Scalar

try:
    from wagtail.rich_text import RichText as WagtailRichText
except ImportError:
    from wagtail.core.rich_text import RichText as WagtailRichText

from ..settings import grapple_settings


class RichText(Scalar):
    @staticmethod
    def serialize(rich_text: str):
        if grapple_settings.RICHTEXT_FORMAT == "html":
            return WagtailRichText(rich_text).__html__()
        return rich_text

    parse_value = str

    @staticmethod
    def parse_literal(node):
        return str(node.value)
