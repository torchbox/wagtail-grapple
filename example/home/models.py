from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import StreamField
from wagtail.core import blocks
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from grapple.models import (
    GraphQLField,
    GraphQLString,
    GraphQLSnippet,
    GrapplePageMixin,
    GraphQLStreamfield,
    GraphQLForeignKey,
)


class HomePage(Page):
    pass


class BlogPage(GrapplePageMixin, Page):
    author = models.CharField(max_length=255)
    date = models.DateField("Post date")
    body = StreamField(
        [
            ("heading", blocks.CharBlock(classname="full title")),
            ("paraagraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("decimal", blocks.DecimalBlock()),
            ("date", blocks.DateBlock()),
            ("datetime", blocks.DateTimeBlock()),
            ("quote", blocks.BlockQuoteBlock()),
            (
                "drink",
                blocks.ChoiceBlock(
                    choices=[("tea", "Tea"), ("coffee", "Coffee")], icon="time"
                ),
            ),
            ("somepage", blocks.PageChooserBlock()),
            (
                "static",
                blocks.StaticBlock(admin_text="Latest posts: no configuration needed."),
            ),
            (
                "person",
                blocks.StructBlock(
                    [
                        ("first_name", blocks.CharBlock()),
                        ("surname", blocks.CharBlock()),
                        ("photo", ImageChooserBlock(required=False)),
                        ("biography", blocks.RichTextBlock()),
                    ],
                    icon="user",
                ),
            ),
            ("video", EmbedBlock()),
            (
                "carousel",
                blocks.StreamBlock(
                    [
                        ("image", ImageChooserBlock()),
                        (
                            "quotation",
                            blocks.StructBlock(
                                [
                                    ("text", blocks.TextBlock()),
                                    ("author", blocks.CharBlock()),
                                ]
                            ),
                        ),
                    ],
                    icon="cogs",
                ),
            ),
            ("doc", DocumentChooserBlock()),
            (
                "ingredients_list",
                blocks.ListBlock(
                    blocks.StructBlock(
                        [
                            ("ingredient", blocks.CharBlock()),
                            ("amount", blocks.CharBlock(required=False)),
                        ]
                    )
                ),
            ),
        ]
    )

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        StreamFieldPanel("body"),
        InlinePanel('related_links', label="Related links"),
    ]

    graphql_fields = [
        GraphQLString("heading"),
        GraphQLString("date"),
        GraphQLString("author"),
        GraphQLStreamfield("body"),
        GraphQLForeignKey("related_links", "home.blogpagerelatedlink", True)
    ]


class BlogPageRelatedLink(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='related_links')
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
    ]

    graphql_fields = [
        GraphQLString('name'),
        GraphQLString('url'),
    ]