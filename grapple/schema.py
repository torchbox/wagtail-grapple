import graphene

from .actions import import_apps
from .types.pages import PagesQuery, PagesSubscription
from .types.images import ImagesQuery
from .types.documents import DocumentsQuery
from .types.snippets import SnippetsQuery
from .types.settings import SettingsQuery
from .types.search import SearchQuery
from .types.streamfield import register_streamfield_blocks
from .registry import registry

"""
Import all the django apps defined in django settings then process each model
in these apps and create graphql node types from them.
"""
import_apps()
register_streamfield_blocks()


"""
Root schema object that graphene is pointed at.
It inherits its queries from each of the specific type mixins.
"""


class Query(
    graphene.ObjectType,
    PagesQuery(),
    ImagesQuery(),
    DocumentsQuery(),
    SnippetsQuery(),
    SettingsQuery(),
    SearchQuery(),
):
    pass


class Subscription(PagesSubscription(), graphene.ObjectType):
    pass


schema = graphene.Schema(
    query=Query, types=list(registry.models.values()), subscription=Subscription
)
