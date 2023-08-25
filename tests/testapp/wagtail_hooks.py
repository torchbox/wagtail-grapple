from wagtail import hooks

from .subscriptions import Subscription


@hooks.register("register_schema_mutation")
def register_mutation_class(mutation_mixins):
    from .mutations import Mutations

    mutation_mixins.append(Mutations)


@hooks.register("register_schema_subscription")
def register_example_subscription(subscription_mixins):
    subscription_mixins.append(Subscription)
