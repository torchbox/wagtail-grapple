from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import StreamField
from wagtail.contrib.settings.models import BaseSetting, register_setting

from wagtail.core import blocks
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.snippets.models import register_snippet
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel

from grapple.models import (
    GraphQLField,
    GraphQLString,
    GraphQLSnippet,
    GrapplePageMixin,
    GraphQLStreamfield,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLDocument,
)


class HomePage(Page):
    pass


class BlogPage(GrapplePageMixin, Page):
    author = models.CharField(max_length=255)
    date = models.DateField("Post date")
    advert = models.ForeignKey(
        'home.Advert',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    cover = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    book_file = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
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
        ImageChooserPanel('cover'),
        StreamFieldPanel("body"),
        InlinePanel('related_links', label="Related links"),
        SnippetChooserPanel('advert'),
        DocumentChooserPanel('book_file'),
    ]

    graphql_fields = [
        GraphQLString("heading"),
        GraphQLString("date"),
        GraphQLString("author"),
        GraphQLStreamfield("body"),
        GraphQLForeignKey("related_links", "home.blogpagerelatedlink", True),
        GraphQLSnippet('advert', 'home.Advert'),
        GraphQLImage('cover'),
        GraphQLDocument('book_file'),
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


@register_snippet
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    graphql_fields = [
        GraphQLString('url'),
        GraphQLString('text')
    ]

    def __str__(self):
        return self.text
        

@register_setting
class SocialMediaSettings(BaseSetting):
    facebook = models.URLField(
        help_text='Your Facebook page URL')
    instagram = models.CharField(
        max_length=255, help_text='Your Instagram username, without the @')
    trip_advisor = models.URLField(
        help_text='Your Trip Advisor page URL')
    youtube = models.URLField(
        help_text='Your YouTube channel or user account URL')

    graphql_fields = [
        GraphQLString('facebook'),
        GraphQLString('instagram'),
        GraphQLString('trip_advisor'),
        GraphQLString('youtube'),
    ]
