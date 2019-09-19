import graphene
from graphql.validation.rules import NoUnusedFragments, specified_rules

# HACK: Remove NoUnusedFragments validator
# Due to the way previews work on the frontend, we need to pass all
# fragments into the query even if they're not used.
# This would usually cause a validation error. There doesn't appear
# to be a nice way to disable this validator so we monkey-patch it instead.


# We need to update specified_rules in-place so the change appears
# everywhere it's been imported

specified_rules[:] = [rule for rule in specified_rules if rule is not NoUnusedFragments]


def create_schema():
    """
    Root schema object that graphene is pointed at.
    It inherits its queries from each of the specific type mixins.
    """
    from .registry import registry
    from .types.documents import DocumentsQuery
    from .types.images import ImagesQuery
    from .types.pages import PagesQuery, PagesSubscription
    from .types.search import SearchQuery
    from .types.settings import SettingsQuery
    from .types.snippets import SnippetsQuery
    from .types.redirects import RedirectsQuery

    class Query(
        graphene.ObjectType,
        PagesQuery(),
        ImagesQuery(),
        DocumentsQuery(),
        SnippetsQuery(),
        SettingsQuery(),
        SearchQuery(),
        RedirectsQuery,
        *registry.schema,
    ):
        pass

    class Subscription(PagesSubscription(), graphene.ObjectType):
        pass

    return graphene.Schema(
        query=Query, types=list(registry.models.values()), subscription=Subscription
    )


schema = create_schema()
