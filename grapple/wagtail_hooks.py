from django.apps import apps
from graphene import ObjectType
from wagtail import hooks

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
