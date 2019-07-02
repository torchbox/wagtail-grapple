import graphene
from graphql.validation.rules import NoUnusedFragments, specified_rules

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

# HACK: Remove NoUnusedFragments validator
# Due to the way previews work on the frontend, we need to pass all
# fragments into the query even if they're not used.
# This would usually cause a validation error. There doesn't appear
# to be a nice way to disable this validator so we monkey-patch it instead.


# We need to update specified_rules in-place so the change appears
# everywhere it's been imported

specified_rules[:] = [
    rule for rule in specified_rules
    if rule is not NoUnusedFragments
]

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
