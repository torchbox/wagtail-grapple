from django.apps import apps
from graphene import ObjectType

try:
    from wagtail import hooks
except ImportError:
    from wagtail.core import hooks

from .registry import registry
from .types.collections import CollectionsQuery
from .types.documents import DocumentsQuery
from .types.images import ImagesQuery
from .types.pages import PagesQuery
from .types.redirects import RedirectsQuery
from .types.search import SearchQuery
from .types.settings import SettingsQuery
from .types.sites import SitesQuery
from .types.snippets import SnippetsQuery
from .types.tags import TagsQuery


@hooks.register("register_schema_query")
def register_schema_query(query_mixins):
    query_mixins += [
        ObjectType,
        PagesQuery(),
        SitesQuery(),
        ImagesQuery(),
        DocumentsQuery(),
        SnippetsQuery(),
        SettingsQuery(),
        SearchQuery(),
        TagsQuery(),
        CollectionsQuery(),
        RedirectsQuery,
    ]

    if apps.is_installed("wagtailmedia"):
        from .types.media import MediaQuery

        query_mixins.append(MediaQuery())

    query_mixins += registry.schema


@hooks.register("register_schema_mutation")
def register_schema_mutation(mutation_mixins):
    mutation_mixins += [ObjectType]


@hooks.register("register_schema_subscription")
def register_schema_subscription(subscription_mixins):
    from .settings import has_channels

    if has_channels:
        from .types.pages import PagesSubscription

        subscription_mixins += [ObjectType, PagesSubscription()]
