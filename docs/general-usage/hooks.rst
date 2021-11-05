Hooks
=====

On loading, Wagtail will search for any app with the file ``wagtail_hooks.py`` and execute the contents.
This provides a way to register your own functions to execute at certain points in Wagtail’s execution. Read more
about hooks in the `Wagtail docs <https://docs.wagtail.io/en/stable/reference/hooks.html>`_


Query
^^^^^

Grapple provides a ``register_schema_query`` hook that is called when it creates the schema. You can use it to
add your custom ``Query`` mixins:

.. code-block:: python

    # your_app/wagtail_hooks.py
    from wagtail.core import hooks
    from your_app.queries import CustomQuery


    @hooks.register("register_schema_query")
    def add_my_custom_query(query_mixins):
        query_mixins.append(
            CustomQuery()
        )  # if defined as mixin, or just CustomQuery if defined as a class


replace or remove any of the default mixins that are not of use in your project:

.. code-block:: python

    # your_app/wagtail_hooks.py
    from wagtail.core import hooks
    from grapple.types.search import SearchQuery
    from .queries import ReplacementQuery


    @hooks.register("register_schema_query")
    def remove_search_query(query_mixins):
        query_mixins[:] = [item for item in query_mixins if item != SearchQuery]


    @hooks.register("register_schema_query")
    def replace_search_query(query_mixins):
        query_mixins[:] = [item for item in query_mixins if item != SearchQuery]
        query_mixins.append(ReplacementQuery)

Mutation
^^^^^^^^

Grapple provides a ``register_schema_mutation`` hook that is called when it creates the schema. You can use it to add your custom ``Mutation`` mixins.

.. code-block:: python

    # your_app/mutations.py
    class CreateAuthor(graphene.Mutation):
        class Arguments:
            name = graphene.String()
            parent = graphene.Int()

        ok = graphene.Boolean()
        author = graphene.Field(
            PageInterface,
        )

        def mutate(root, info, name, parent):
            author = AuthorPage(name=name, title=name, slug=name)
            ok = True
            Page.objects.get(id=parent).add_child(instance=author)
            author.save_revision().publish()
            return CreateAuthor(author=author, ok=ok)


    class Mutation(graphene.ObjectType):
        create_author = CreateAuthor.Field()


.. code-block:: python

    # your_app/wagtail_hooks.py
    from .mutations import Mutation


    @hooks.register("register_schema_mutation")
    def register_author_mutation(mutation_mixins):
        mutation_mixins.append(Mutation)


Subscription
^^^^^^^^^^^^

Note: subscriptions are only enabled when Grapple is installed with Django Channels: ``pip install wagtail_grapple[channels]``.
Grapple provides a ``register_schema_subscription`` hook that is called when it creates the schema. You can use it to add your custom ``Subscription`` mixins

.. code-block:: python

    # your_app/subscriptions.py
    import graphene
    from rx import Observable


    class Subscription(graphene.ObjectType):
        hello = graphene.String()

        def resolve_hello(root, info):
            return Observable.interval(3000).map(lambda i: "hello world!")


.. code-block:: python

    # your_app/wagtail_hooks.py
    from .subscriptions import Subscription


    @hooks.register("register_schema_subscription")
    def register_example_subscription(subscription_mixins):
        subscription_mixins.append(Subscription)
