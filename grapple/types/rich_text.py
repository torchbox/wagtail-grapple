from django.template.loader import render_to_string
from graphene.types import Scalar

try:
    from wagtail.rich_text import expand_db_html
except ImportError:
    from wagtail.core.rich_text import expand_db_html

from ..settings import grapple_settings


class RichText(Scalar):
    @staticmethod
    def serialize(rich_text: str):
        if grapple_settings.RICHTEXT_FORMAT == "html":
            return render_to_string(
                "wagtailcore/richtext.html", context={"html": expand_db_html(rich_text)}
            )
        return rich_text
