import graphene

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet
from wagtail_headless_preview.models import HeadlessPreviewMixin
from wagtailmedia.edit_handlers import MediaChooserPanel

from grapple.helpers import (
    register_paginated_query_field,
    register_query_field,
    register_singular_query_field,
)
from grapple.middleware import IsAnonymousMiddleware
from grapple.models import (
    GraphQLCollection,
    GraphQLDocument,
    GraphQLField,
    GraphQLForeignKey,
    GraphQLImage,
    GraphQLMedia,
    GraphQLPage,
    GraphQLRichText,
    GraphQLSnippet,
    GraphQLStreamfield,
    GraphQLString,
    GraphQLTag,
)
from grapple.utils import resolve_paginated_queryset
from testapp.blocks import StreamFieldBlock
from testapp.interfaces import CustomInterface


document_model_string = getattr(
    settings, "WAGTAILDOCS_DOCUMENT_MODEL", "wagtaildocs.Document"
)


@register_singular_query_field("simpleModel")
class SimpleModel(models.Model):
    graphql_interfaces = (CustomInterface,)


def custom_middleware_one(next, root, info, **args):
    info.context.custom_middleware_one = True
    return next(root, info, **args)


def custom_middleware_two(next, root, info, **args):
    if not info.context.custom_middleware_one:
        raise Exception("Middleware one should have been called")
    if args["id"] == 2:
        return None
    return next(root, info, **args)


@register_query_field(
    "middlewareModel", middleware=[custom_middleware_one, custom_middleware_two]
)
class MiddlewareModel(models.Model):
    pass


class HomePage(Page):
    pass


class AuthorPage(Page):
    name = models.CharField(max_length=255)

    content_panels = Page.content_panels + [FieldPanel("name")]

    graphql_fields = [GraphQLString("name")]
    graphql_interfaces = (CustomInterface,)


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "BlogPage", related_name="tagged_items", on_delete=models.CASCADE
    )


@register_singular_query_field("first_post", middleware=[IsAnonymousMiddleware])
@register_paginated_query_field("blog_page", middleware=[IsAnonymousMiddleware])
@register_query_field(
    "post", middleware=[IsAnonymousMiddleware()]
)  # instantiated on purpose
class BlogPage(HeadlessPreviewMixin, Page):
    date = models.DateField("Post date")
    advert = models.ForeignKey(
        "testapp.Advert",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_image = models.ForeignKey(
        "testapp.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    book_file = models.ForeignKey(
        document_model_string,
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
    summary = RichTextField(blank=True)
    extra_summary = RichTextField(blank=True)
    body = StreamField(StreamFieldBlock(), use_json_field=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("hero_image"),
        FieldPanel("summary"),
        FieldPanel("body"),
        FieldPanel("tags"),
        InlinePanel("related_links", label="Related links"),
        InlinePanel("authors", label="Authors"),
        FieldPanel("author"),
        FieldPanel("advert"),
        FieldPanel("book_file"),
        MediaChooserPanel("featured_media"),
    ]

    @property
    def copy(self):
        return self

    def paginated_authors(self, info, **kwargs):
        return resolve_paginated_queryset(self.authors, info, **kwargs)

    @cached_property
    def custom_property(self):
        return {
            "path": self.url,
            "author": self.author.name if self.author else "Unknown",
        }

    graphql_fields = [
        GraphQLString("date", required=True),
        GraphQLRichText("summary"),
        GraphQLString("string_summary", source="summary"),
        GraphQLString("extra_summary", deprecation_reason="Use summary instead"),
        GraphQLField(
            field_name="custom_property",
            field_type=graphene.JSONString,
            required=False,
        ),
        GraphQLStreamfield("body"),
        GraphQLTag("tags"),
        GraphQLCollection(
            GraphQLForeignKey,
            "related_links",
            "testapp.BlogPageRelatedLink",
            required=True,
            item_required=True,
        ),
        GraphQLCollection(GraphQLString, "related_urls", source="related_links.url"),
        GraphQLCollection(GraphQLString, "authors", source="authors.person.name"),
        GraphQLCollection(
            GraphQLForeignKey,
            "paginated_authors",
            "testapp.Author",
            is_paginated_queryset=True,
        ),
        GraphQLSnippet("advert", "testapp.Advert"),
        GraphQLImage("hero_image"),
        GraphQLDocument("book_file"),
        GraphQLMedia("featured_media"),
        GraphQLForeignKey("copy", "testapp.BlogPage"),
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

    panels = [FieldPanel("role"), FieldPanel("person")]

    graphql_fields = [GraphQLString("role"), GraphQLForeignKey("person", Person)]


def custom_middleware(next, root, info, **kwargs):
    info.context.custom_middleware = True
    return next(root, info, **kwargs)


@register_snippet
@register_query_field(
    "advert",
    "adverts",
    query_params={"url": graphene.String()},
    required=True,
    plural_required=True,
    plural_item_required=True,
    middleware=[custom_middleware],
)
class Advert(models.Model):
    url = models.URLField(blank=True)
    text = models.CharField(max_length=255)
    rich_text = RichTextField(blank=True, default="")
    extra_rich_text = RichTextField(blank=True, default="")

    panels = [FieldPanel("url"), FieldPanel("text"), FieldPanel("rich_text")]

    graphql_fields = [
        GraphQLString("url"),
        GraphQLString("text"),
        GraphQLRichText("rich_text"),
        GraphQLString("string_rich_text", source="rich_text"),
        GraphQLString("extra_rich_text", deprecation_reason="Use rich_text instead"),
    ]
    graphql_interfaces = (CustomInterface,)

    def __str__(self):
        return self.text


@register_setting
class SocialMediaSettings(BaseSiteSetting):
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


class GlobalSocialMediaSettings(BaseGenericSetting):
    facebook = models.URLField(help_text="Your Facebook page URL")
    instagram = models.CharField(
        max_length=255, help_text="Your Instagram username, without the @"
    )
    trip_advisor = models.URLField(help_text="Your Trip Advisor page URL")
    youtube = models.URLField(help_text="Your YouTube channel or user account URL")

    graphql_fields = [
        GraphQLString("facebook"),
        GraphQLString(
            "instagram",
            description="Provides an Instagram account username, without the @",
        ),
        GraphQLString("trip_advisor"),
        GraphQLString("youtube", deprecation_reason="No longer supported"),
    ]


register_setting(GlobalSocialMediaSettings)
