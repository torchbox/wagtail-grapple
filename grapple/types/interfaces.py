import inspect

import graphene

from django.contrib.contenttypes.models import ContentType
from django.utils.module_loading import import_string
from graphql import GraphQLError
from wagtail import blocks
from wagtail.models import Page as WagtailPage
from wagtail.rich_text import RichText

from ..registry import registry
from ..settings import grapple_settings
from ..utils import resolve_queryset, serialize_struct_obj
from .structures import QuerySetList


def get_page_interface():
    return import_string(grapple_settings.PAGE_INTERFACE)


class PageInterface(graphene.Interface):
    id = graphene.ID()
    title = graphene.String(required=True)
    slug = graphene.String(required=True)
    content_type = graphene.String(required=True)
    page_type = graphene.String()
    live = graphene.Boolean(required=True)

    url = graphene.String()
    url_path = graphene.String(required=True)

    depth = graphene.Int()
    seo_title = graphene.String(required=True)
    search_description = graphene.String()
    show_in_menus = graphene.Boolean(required=True)

    locked = graphene.Boolean()

    first_published_at = graphene.DateTime()
    last_published_at = graphene.DateTime()

    parent = graphene.Field(get_page_interface)
    children = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )
    siblings = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )
    next_siblings = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )
    previous_siblings = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )
    descendants = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )
    ancestors = QuerySetList(
        graphene.NonNull(get_page_interface),
        enable_search=True,
        required=True,
        enable_in_menu=True,
    )

    search_score = graphene.Float()

    @classmethod
    def resolve_type(cls, instance, info, **kwargs):
        """
        If model has a custom Graphene Node type in registry then use it,
        otherwise use base page type.
        """
        from .pages import Page

        return registry.pages.get(type(instance), Page)

    def resolve_content_type(self, info, **kwargs):
        self.content_type = ContentType.objects.get_for_model(self)
        return (
            f"{self.content_type.app_label}.{self.content_type.model_class().__name__}"
        )

    def resolve_page_type(self, info, **kwargs):
        return get_page_interface().resolve_type(self.specific, info, **kwargs)

    def resolve_parent(self, info, **kwargs):
        """
        Resolves the parent node of current page node.
        Docs: https://docs.wagtail.io/en/stable/reference/pages/model_reference.html#wagtail.models.Page.get_parent
        """
        try:
            return self.get_parent().specific
        except GraphQLError:
            return WagtailPage.objects.none()

    def resolve_children(self, info, **kwargs):
        """
        Resolves a list of live children of this page.
        Docs: https://docs.wagtail.io/en/stable/reference/pages/queryset_reference.html#examples
        """
        return resolve_queryset(
            self.get_children().live().public().specific(), info, **kwargs
        )

    def resolve_siblings(self, info, **kwargs):
        """
        Resolves a list of sibling nodes to this page.
        Docs: https://docs.wagtail.io/en/stable/reference/pages/queryset_reference.html?highlight=get_siblings#wagtail.query.PageQuerySet.sibling_of
        """
        return resolve_queryset(
            self.get_siblings().exclude(pk=self.pk).live().public().specific(),
            info,
            **kwargs,
        )

    def resolve_next_siblings(self, info, **kwargs):
        """
        Resolves a list of direct next siblings of this page. Similar to `resolve_siblings` with sorting.
        Source: https://github.com/wagtail/wagtail/blob/master/wagtail/core/models.py#L1384
        """
        return resolve_queryset(
            self.get_next_siblings().exclude(pk=self.pk).live().public().specific(),
            info,
            **kwargs,
        )

    def resolve_previous_siblings(self, info, **kwargs):
        """
        Resolves a list of direct prev siblings of this page. Similar to `resolve_siblings` with sorting.
        Source: https://github.com/wagtail/wagtail/blob/master/wagtail/core/models.py#L1387
        """
        return resolve_queryset(
            self.get_prev_siblings().exclude(pk=self.pk).live().public().specific(),
            info,
            **kwargs,
        )

    def resolve_descendants(self, info, **kwargs):
        """
        Resolves a list of nodes pointing to the current page’s descendants.
        Docs: https://docs.wagtail.io/en/stable/reference/pages/model_reference.html#wagtail.models.Page.get_descendants
        """
        return resolve_queryset(
            self.get_descendants().live().public().specific(), info, **kwargs
        )

    def resolve_ancestors(self, info, **kwargs):
        """
        Resolves a list of nodes pointing to the current page’s ancestors.
        Docs: https://docs.wagtail.io/en/stable/reference/pages/model_reference.html#wagtail.models.Page.get_ancestors
        """
        return resolve_queryset(
            self.get_ancestors().live().public().specific(), info, **kwargs
        )

    def resolve_seo_title(self, info, **kwargs):
        """
        Get page's SEO title. Fallback to a normal page's title if absent.
        """
        return self.seo_title or self.title

    def resolve_search_score(self, info, **kwargs):
        """
        Get page's search score, will be None if not in a search context.
        """
        return getattr(self, "search_score", None)


class StreamFieldInterface(graphene.Interface):
    id = graphene.String()
    block_type = graphene.String(required=True)
    field = graphene.String(required=True)
    raw_value = graphene.String(required=True)

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
        if isinstance(self, blocks.StructValue):
            # This is the value for a nested StructBlock defined via GraphQLStreamfield
            return serialize_struct_obj(self)
        elif isinstance(self.value, dict):
            return serialize_struct_obj(self.value)
        elif isinstance(self.value, RichText):
            # Ensure RichTextBlock raw value always returns the "internal format", rather than the conterted value
            # as per https://docs.wagtail.io/en/stable/extending/rich_text_internals.html#data-format.
            # Note that RichTextBlock.value will be rendered HTML by default.
            return self.value.source

        return self.value


def get_snippet_interface():
    return import_string(grapple_settings.SNIPPET_INTERFACE)


class SnippetInterface(graphene.Interface):
    snippet_type = graphene.String(required=True)
    content_type = graphene.String(required=True)

    @classmethod
    def resolve_type(cls, instance, info, **kwargs):
        return registry.snippets[type(instance)]

    def resolve_snippet_type(self, info, **kwargs):
        return self.__class__.__name__

    def resolve_content_type(self, info, **kwargs):
        self.content_type = ContentType.objects.get_for_model(self)
        return (
            f"{self.content_type.app_label}.{self.content_type.model_class().__name__}"
        )
