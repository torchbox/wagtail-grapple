import graphene
from graphql.validation.rules import NoUnusedFragments, specified_rules

try:
    from wagtail import hooks
except ImportError:
    from wagtail.core import hooks

from .registry import registry
from .settings import grapple_settings

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

    from .settings import has_channels

    query_mixins = []
    for fn in hooks.get_hooks("register_schema_query"):
        fn(query_mixins)

    # ensure graphene.ObjectType is always present
    if graphene.ObjectType not in query_mixins:
        query_mixins.append(graphene.ObjectType)

    class Query(*query_mixins):
        pass

    mutation_mixins = []
    for fn in hooks.get_hooks("register_schema_mutation"):
        fn(mutation_mixins)

    # ensure graphene.ObjectType is always present
    if graphene.ObjectType not in mutation_mixins:
        mutation_mixins.append(graphene.ObjectType)

    if len(mutation_mixins) > 1:

        class Mutation(*mutation_mixins):
            pass

    else:
        Mutation = None

    if has_channels:
        subscription_mixins = []
        for fn in hooks.get_hooks("register_schema_subscription"):
            fn(subscription_mixins)

        # ensure graphene.ObjectType is always present
        if graphene.ObjectType not in subscription_mixins:
            subscription_mixins.append(graphene.ObjectType)

        if len(subscription_mixins) > 1:

            class Subscription(*subscription_mixins):
                pass

        else:
            Subscription = None

    else:
        Subscription = None

    return graphene.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        types=list(registry.models.values()),
        auto_camelcase=grapple_settings.AUTO_CAMELCASE,
    )


schema = create_schema()
