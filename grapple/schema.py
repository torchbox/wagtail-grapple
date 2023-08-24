import graphene

from graphql.validation import NoUnusedFragmentsRule
from wagtail import hooks

from .registry import registry
from .settings import grapple_settings


# HACK: Remove NoUnusedFragments validator
# Due to the way previews work on the frontend, we need to pass all
# fragments into the query even if they're not used.
# This would usually cause a validation error. There doesn't appear
# to be a nice way to disable this validator so we monkey-patch it instead.


# We can't simply override specified_rules because it's a tuple and immutable. Instead, we are
# monkey patching the NoUnusedFragmentRule.leave_document, so it doesn't do any validation.
NoUnusedFragmentsRule.leave_document = lambda self, *_args: None


def create_schema():
    """
    Root schema object that graphene is pointed at.
    It inherits its queries from each of the specific type mixins.
    """

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

    if len(mutation_mixins) > 0:

        class Mutation(*mutation_mixins):
            pass

    else:
        Mutation = None

    subscription_mixins = []
    for fn in hooks.get_hooks("register_schema_subscription"):
        fn(subscription_mixins)

    if len(subscription_mixins) > 0:
        # ensure graphene.ObjectType is always present
        if graphene.ObjectType not in subscription_mixins:
            subscription_mixins.append(graphene.ObjectType)

        class Subscription(*subscription_mixins):
            pass

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
