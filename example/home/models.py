from __future__ import unicode_literals
from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import StreamField
from wagtail.contrib.settings.models import BaseSetting, register_setting

from wagtail.core import blocks
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.snippets.models import register_snippet
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel

from wagtail_headless_preview.models import HeadlessPreviewMixin
from wagtailmedia.edit_handlers import MediaChooserPanel

from grapple.models import (
    GraphQLField,
    GraphQLString,
    GraphQLSnippet,
    GraphQLStreamfield,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLDocument,
    GraphQLMedia,
    GraphQLCollection,
    GraphQLPage,
)
from home.blocks import StreamFieldBlock


class HomePage(Page):
    pass


class AuthorPage(Page):
    name = models.CharField(max_length=255)

    content_panels = Page.content_panels + [FieldPanel("name")]

    graphql_fields = [GraphQLString("name")]


class BlogPage(HeadlessPreviewMixin, Page):
    date = models.DateField("Post date")
    advert = models.ForeignKey(
        "home.Advert",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    cover = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    book_file = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    featured_media = models.ForeignKey(
        "wagtailmedia.Media",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    author = models.ForeignKey(
        AuthorPage, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    body = StreamField(StreamFieldBlock())

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        ImageChooserPanel("cover"),
        StreamFieldPanel("body"),
        InlinePanel("related_links", label="Related links"),
        InlinePanel("authors", label="Authors"),
        FieldPanel("author"),
        SnippetChooserPanel("advert"),
        DocumentChooserPanel("book_file"),
        MediaChooserPanel("featured_media"),
    ]

    @property
    def copy(self):
        return self

    graphql_fields = [
        GraphQLString("heading"),
        GraphQLString("date"),
        GraphQLStreamfield("body"),
        GraphQLCollection(
            GraphQLForeignKey, "related_links", "home.blogpagerelatedlink"
        ),
        GraphQLCollection(GraphQLString, "related_urls", source="related_links.url"),
        GraphQLCollection(GraphQLString, "authors", source="authors.person.name"),
        GraphQLSnippet("advert", "home.Advert"),
        GraphQLImage("cover"),
        GraphQLDocument("book_file"),
        GraphQLMedia("featured_media"),
        GraphQLForeignKey("copy", "home.BlogPage"),
        GraphQLPage("author"),
    ]


class BlogPageRelatedLink(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name="related_links")
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [FieldPanel("name"), FieldPanel("url")]

    graphql_fields = [GraphQLString("name"), GraphQLString("url")]


@register_snippet
class Person(models.Model):
    name = models.CharField(max_length=255)
    job = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    panels = [FieldPanel("name"), FieldPanel("job")]

    graphql_fields = [GraphQLString("name"), GraphQLString("job")]


class Author(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name="authors")
    role = models.CharField(max_length=255)
    person = models.ForeignKey(
        Person, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    panels = [FieldPanel("role"), SnippetChooserPanel("person")]

    graphql_fields = [GraphQLString("role"), GraphQLForeignKey("person", Person)]


@register_snippet
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [FieldPanel("url"), FieldPanel("text")]

    graphql_fields = [GraphQLString("url"), GraphQLString("text")]

    def __str__(self):
        return self.text


@register_setting
class SocialMediaSettings(BaseSetting):
    facebook = models.URLField(help_text="Your Facebook page URL")
    instagram = models.CharField(
        max_length=255, help_text="Your Instagram username, without the @"
    )
    trip_advisor = models.URLField(help_text="Your Trip Advisor page URL")
    youtube = models.URLField(help_text="Your YouTube channel or user account URL")

    graphql_fields = [
        GraphQLString("facebook"),
        GraphQLString("instagram"),
        GraphQLString("trip_advisor"),
        GraphQLString("youtube"),
    ]



from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList

from wagtail.core import blocks
from wagtail.core.blocks import ChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

from grapple.helpers import register_streamfield_block
from grapple.models import (
    GraphQLBoolean,
    GraphQLCollection,
    GraphQLEmbed,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLInt,
    GraphQLString,
)
from wagtailvideos.models import Video
from wagtailvideos.widgets import AdminVideoChooser

ICON_CHOICES = (("certificate", "Certificate"), ("pitch", "Pitch"), ("timer", "Timer"))


@register_streamfield_block
class TimelineEntry(blocks.StructBlock):
    image = ImageChooserBlock(
        help_text="Recommended image size 1400x787-2000x1125px (16:9), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated."
    )
    title = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])

    class Meta:
        icon = "image"

    graphql_fields = [GraphQLImage("image"), GraphQLString("title")]


@register_streamfield_block
class TimelineBlock(blocks.StreamBlock):
    entry = TimelineEntry()

    class Meta:
        min_num = 2
        max_num = 6
        icon = "image"

    graphql_fields = [GraphQLForeignKey("entry", TimelineEntry, is_list=True)]


@register_streamfield_block
class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(
        help_text="Recommended image size 1400x787-2000x1125px (16:9), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated."
    )
    caption = blocks.RichTextBlock(
        features=["bold", "italic", "link", "underline"], required=False
    )

    class Meta:
        icon = "image"

    graphql_fields = [GraphQLImage("image"), GraphQLString("caption")]


@register_streamfield_block
class QuoteBlock(blocks.StructBlock):
    quote = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])
    attribution = blocks.RichTextBlock(
        features=["bold", "italic", "link", "underline"], required=False
    )
    image = ImageChooserBlock(
        required=False,
        help_text="Recommended image size 1400x787-2000x1125px (16:9), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )

    class Meta:
        icon = "openquote"

    graphql_fields = [
        GraphQLImage("image"),
        GraphQLString("quote"),
        GraphQLString("attribution"),
    ]


@register_streamfield_block
class TextAndNumberResult(blocks.StructBlock):
    icon = blocks.ChoiceBlock(required=False, choices=ICON_CHOICES)
    number = blocks.DecimalBlock()
    text = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])

    class Meta:
        icon = "pilcrow"

    graphql_fields = [
        GraphQLString("text"),
        GraphQLString("number_prefix"),
        GraphQLString("number_suffix"),
        GraphQLString("icon"),
        GraphQLInt("number"),
    ]


@register_streamfield_block
class TextAndNumberResults(blocks.StreamBlock):
    text_and_number_result = TextAndNumberResult()

    class Meta:
        max_num = 3
        icon = "pilcrow"


@register_streamfield_block
class ResultsTextAndNumberBlock(blocks.StructBlock):
    title = blocks.CharBlock(default="Results - Text and Number")
    text_and_number_results = TextAndNumberResults()

    class Meta:
        icon = "pilcrow"

    graphql_fields = [
        GraphQLString("title"),
        GraphQLCollection(
            GraphQLForeignKey, "text_and_number_results", TextAndNumberResult
        ),
    ]


@register_streamfield_block
class ChartResult(blocks.StructBlock):
    percentage = blocks.IntegerBlock()
    text = blocks.CharBlock()

    class Meta:
        icon = "table"

    graphql_fields = [GraphQLString("text"), GraphQLInt("percentage")]


@register_streamfield_block
class ChartResults(blocks.StreamBlock):
    chart_result = ChartResult()

    class Meta:
        max_num = 3
        icon = "table"


@register_streamfield_block
class ResultsChartBlock(blocks.StructBlock):
    title = blocks.CharBlock(default="Results - Chart")
    chart_results = ChartResults()

    class Meta:
        icon = "table"

    graphql_fields = [
        GraphQLString("title"),
        GraphQLCollection(GraphQLForeignKey, "chart_results", ChartResult),
    ]


@register_streamfield_block
class ComparisonChartResult(blocks.StructBlock):
    number1 = blocks.IntegerBlock()
    text1 = blocks.CharBlock()
    number2 = blocks.IntegerBlock()
    text2 = blocks.CharBlock()
    show_as_percentage = blocks.BooleanBlock(
        default=True,
        help="This will calculate the percentage from the given numbers assuming number1 + number2 = 100%",
    )

    class Meta:
        icon = "table"

    graphql_fields = [
        GraphQLString("text1"),
        GraphQLInt("number1"),
        GraphQLString("text2"),
        GraphQLInt("number2"),
        GraphQLBoolean("show_as_percentage"),
    ]


@register_streamfield_block
class ComparisonChartResults(blocks.StreamBlock):
    comparison_chart_result = ComparisonChartResult()

    class Meta:
        max_num = 3
        icon = "table"


@register_streamfield_block
class ResultsComparisonChartBlock(blocks.StructBlock):
    title = blocks.CharBlock(default="Results - Comparison Chart")
    comparison_chart_results = ComparisonChartResults()

    class Meta:
        icon = "table"

    graphql_fields = [
        GraphQLString("title"),
        GraphQLCollection(
            GraphQLForeignKey, "comparison_chart_results", ComparisonChartResult
        ),
    ]


@register_streamfield_block
class StoryScrollerIntro(blocks.StructBlock):
    title = blocks.CharBlock()
    text = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])
    background = ImageChooserBlock(
        required=True,
        help_text="Recommended image size 743x787-1063x1125px (17:18), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )

    class Meta:
        icon = "pilcrow"

    graphql_fields = [
        GraphQLString("title"),
        GraphQLString("text"),
        GraphQLImage("background"),
    ]


@register_streamfield_block
class StoryScrollerQuote(blocks.StructBlock):
    quote = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])
    attribution = blocks.RichTextBlock(
        features=["bold", "italic", "link", "underline"], required=False
    )
    background = ImageChooserBlock(
        required=False,
        help_text="Recommended image size 743x787-1063x1125px (17:18), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )

    class Meta:
        icon = "openquote"

    graphql_fields = [
        GraphQLString("quote"),
        GraphQLString("attribution"),
        GraphQLImage("background"),
    ]


@register_streamfield_block
class StoryScrollerStatistic(blocks.StructBlock):
    statistic = blocks.CharBlock()
    text = blocks.RichTextBlock(
        features=["bold", "italic", "link", "underline"],
        help_text="Describe the given statistic",
    )
    background = ImageChooserBlock(
        required=False,
        help_text="Recommended image size 743x787-1063x1125px (17:18), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )

    class Meta:
        icon = "pilcrow"

    graphql_fields = [
        GraphQLString("statistic"),
        GraphQLString("text"),
        GraphQLImage("background"),
    ]


@register_streamfield_block
class StoryScrollerSlides(blocks.StreamBlock):
    intro = StoryScrollerIntro()
    quote = StoryScrollerQuote()
    statistic = StoryScrollerStatistic()

    class Meta:
        icon = "pilcrow"

    graphql_types = [StoryScrollerIntro, StoryScrollerQuote, StoryScrollerStatistic]


@register_streamfield_block
class StoryScrollerGallery(blocks.StreamBlock):
    images = ImageBlock()

    class Meta:
        icon = "pilcrow"

    graphql_types = [ImageBlock]


@register_streamfield_block
class StoryScrollerBlock(blocks.StructBlock):
    slides = StoryScrollerSlides()
    extra_images = StoryScrollerGallery(required=False)

    graphql_fields = [
        GraphQLCollection(GraphQLForeignKey, "slides", StoryScrollerSlides),
        GraphQLCollection(GraphQLForeignKey, "extra_images", ImageBlock),
    ]


class VideoChooserBlock(ChooserBlock):
    target_model = Video
    widget = AdminVideoChooser

    def render_basic(self, value, context=None):
        if not value:
            return ""
        return value.file.url

    class Meta:
        icon = "media"


@register_streamfield_block
class VideoBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    youtube_link = EmbedBlock(required=False)
    video_upload = VideoChooserBlock(required=False)

    def clean(self, value):
        errors = {}
        if value["youtube_link"] and value["video_upload"]:
            errors["youtube_link"] = ErrorList(
                ["Select only one out of youtube link and video upload"]
            )

        if not (value["youtube_link"] or value["video_upload"]):
            errors["youtube_link"] = ErrorList(
                ["Select either youtube link or video upload"]
            )

        if errors:
            raise ValidationError("Validation error in VideoBlock", params=errors)
        return super(VideoBlock, self).clean(value)

    class Meta:
        icon = "media"

    def get_embed_block(self):
        return self.youtube_link

    graphql_fields = [
        GraphQLString("title"),
        GraphQLEmbed("youtube_link"),
        GraphQLEmbed("video_upload"),
    ]


# Main streamfield block to be inherited by Pages
@register_streamfield_block
class StoryBlock(blocks.StreamBlock):
    text = blocks.RichTextBlock(features=["bold", "italic", "link", "underline"])
    quote = QuoteBlock()
    results_text_number = ResultsTextAndNumberBlock()
    results_chart = ResultsChartBlock()
    results_comparison_chart = ResultsComparisonChartBlock()
    timeline = TimelineBlock()
    image = ImageBlock()
    story_scroller = StoryScrollerBlock()
    video = VideoBlock()


class Story(HeadlessPreviewMixin, Page):
    subtitle = models.CharField(max_length=255)
    cover_logo = models.ForeignKey(
        "images.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="If empty, this will be your organisation's logo.",
    )
    cover_image = models.ForeignKey(
        "images.CustomImage",
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Recommended image size 1400x787-2000x1125px (16:9), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )
    thank_you_text = RichTextField(features=["bold", "italic", "link", "underline"])
    thank_you_image = models.ForeignKey(
        "images.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Recommended image size 1400x787-2000x1125px (16:9), smaller"
        " images won't have as much of an impact and portrait images will"
        " be manipulated.",
    )
    body = StreamField(StoryBlock())

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        ImageChooserPanel("cover_logo"),
        ImageChooserPanel("cover_image"),
        FieldPanel("thank_you_text"),
        ImageChooserPanel("thank_you_image"),
    ]

    graphql_fields = [
        GraphQLStreamfield("body"),
        GraphQLString("subtitle"),
        GraphQLString("facebook_app_id"),
        GraphQLImage("get_cover_logo"),
        GraphQLImage("cover_image"),
        GraphQLString("thank_you_text"),
        GraphQLImage("thank_you_image"),
    ]

