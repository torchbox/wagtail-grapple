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
    from wagtail import hooks
    from your_app.queries import CustomQuery


    @hooks.register("register_schema_query")
    def add_my_custom_query(query_mixins):
        query_mixins.append(
            CustomQuery()
        )  # if defined as mixin, or just CustomQuery if defined as a class


replace or remove any of the default mixins that are not of use in your project:

.. code-block:: python

    # your_app/wagtail_hooks.py
    from wagtail import hooks
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

Note: previously subscriptions were only enabled when Grapple was installed with Django Channels. We no longer provide
out of the box support for subscriptions due to incompatibilities in the various dependencies.
The ``register_schema_subscription`` hook is still provided. It is called when Grapple creates the schema.
You can use it to add your custom ``Subscription`` mixins and functionality.

.. code-block:: python

    import asyncio
    import graphene


    class Subscription(graphene.ObjectType):
        count_seconds = graphene.String()

        async def resolve_count_seconds(root, info, up_to):
            for i in range(up_to):
                yield i
                await asyncio.sleep(1.0)
            yield up_to



.. code-block:: python

    # your_app/wagtail_hooks.py
    from .subscriptions import Subscription


    @hooks.register("register_schema_subscription")
    def register_example_subscription(subscription_mixins):
        subscription_mixins.append(Subscription)
