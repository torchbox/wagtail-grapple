import graphene

from django.conf import settings
from graphql.validation.rules import NoUnusedFragments, specified_rules
from wagtail.core import hooks

from .registry import registry


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

    from .types.pages import has_channels

    query_mixins = []
    for fn in hooks.get_hooks("register_schema_query"):
        fn(query_mixins)

    # ensure graphene.ObjectType is always present
    if graphene.ObjectType not in query_mixins:
        query_mixins.append(graphene.ObjectType)

    class Query(*query_mixins):
        pass

    if has_channels:
        from .types.pages import PagesSubscription

        class Subscription(PagesSubscription(), graphene.ObjectType):
            pass

    else:
        Subscription = None

    return graphene.Schema(
        query=Query,
        subscription=Subscription,
        types=list(registry.models.values()),
        auto_camelcase=getattr(settings, "GRAPPLE_AUTO_CAMELCASE", True),
    )


schema = create_schema()
