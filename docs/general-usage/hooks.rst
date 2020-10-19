Hooks
=====

On loading, Wagtail will search for any app with the file ``wagtail_hooks.py`` and execute the contents.
This provides a way to register your own functions to execute at certain points in Wagtail’s execution. Read more
about hooks in the `Wagtail docs <https://docs.wagtail.io/en/stable/reference/hooks.html>`_

Grapple provides a ``register_schema_query`` hook that is called when it creates the schema. You can use it to
add your custom ``Query`` mixins:

.. code-block:: python
    from wagtail.core import hooks
    from mypackage.queries import CustomQuery

    @hooks.register('register_schema_query')
    def add_my_custom_query(query_mixins):
        query_mixins.append(CustomQuery())  # if defined as mixin, or just CustomQuery if defined as a class


replace or remove any of the default mixins that are not of use in your project:

.. code-block:: python
    from wagtail.core import hooks
    from grapple.types.search import SearchQuery
    from mypackage.queries import ReplacementQuery

    @hooks.register('register_schema_query')
    def remove_search_query(query_mixins):
        query_mixins[:] = [item for item in query_mixins if item != SearchQuery]

    @hooks.register('register_schema_query')
    def replace_search_query(query_mixins):
        query_mixins[:] = [item for item in query_mixins if item != SearchQuery]
        quer_mixins.append(ReplacementQuery)
