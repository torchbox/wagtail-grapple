Interfaces
==========

Out of the box, Grapple generates the schema with the following GraphQL interfaces:

- ``PageInterface`` for Wagtail ``Page`` models
- ``StreamFieldInterface`` for Wagtail ``StreamField`` block models

``PageInterface``
-----------------

The default GraphQL interface for all Wagtail ``Page``-derived models.

This is accessible through the ``pages`` or ``page`` field on the root query type.

The interface exposes the following fields, following the Wagtail Page model fields and properties:

::

    id: ID
    url: String
    slug: String
    depth: Int
    pageType: String
    title: String
    seoTitle: String
    seoDescription: String
    showInMenus: Boolean
    contentType: String
    parent: PageInterface
    children(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]
    siblings(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]
    nextSiblings(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]
    previousSiblings(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]
    descendants(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]
    ancestors(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]


Any custom ``graphql_fields`` added to your specific Page models will be available here via the 'on' spread operator and
the name of the model:

::

    query {
        pages {
            ...on BlogPage {
                the_custom_field
            }
        }
    }

You can change the default ``PageInterface`` to your own interface by changing the
:ref:`PAGE_INTERFACE<page interface settings>` setting.

As mentioned above there is both a plural ``pages`` and singular ``page``
field on the root Query type that returns a ``PageInterface``.

The plural ``pages`` field (as do all plural fields)
accepts the following arguments:

::

    id: ID
    limit: PositiveInt
    offset: PositiveInt
    order: String
    searchQuery: String
    contentType: String           #  comma separated list of content types in app.Model notation
    inSite: Boolean
    ancestor: PositiveInt         # ID of ancestor page to restrict results to
    parent: PositiveInt           # ID of parent page to restrict results to


The singular ``page`` field accepts the following arguments:

::

    id: ID                        # Can be used on it's own
    slug: String                  # Can be used on it's own
    urlPath: String               # Can be used on it's own
    token: String                 # Must be used with one of the others. Usually contentType
    contentType: String           # Can be used on it's own
    inSite: Boolean               # Can be used on it's own



``StreamFieldInterface``
------------------------

``StreamFieldInterface`` is the default interface for all Wagtail StreamField block models. It exposes the following
fields, following the base fields and properties available to the Wagtail StreamField blocks:

::

    id: ID
    blockType: String!
    field: String!
    rawValue: String!

Note that blocks subclassing `StreamBlock <https://docs.wagtail.org/en/stable/topics/streamfield.html#streamblock>`_
and `StructBlock <https://docs.wagtail.org/en/stable/topics/streamfield.html#structblock>`_ have an additional property
in the interface:

::

    blocks: [StreamFieldInterface!]!  # a list of blocks in the StreamBlock or StructBlock



Adding your own interfaces
--------------------------

To add additional interfaces to your model, define the ``graphql_interfaces`` attribute on it. The attribute can be
a list of interfaces (``graphql_interfaces = [MyInterface]``) or a tuple (``graphql_interfaces = (MyInterface, )``).

Given the following example interface:

.. code-block:: python

    # interfaces.py
    from .interfaces import CustomInterface


    class CustomInterface(graphene.Interface):
        custom_field = graphene.String()

you could add it to your Page model like so:

.. code-block:: python

    from wagtail.models import Page


    class MyPage(Page):
        # ...

        graphql_interfaces = (CustomInterface,)

or any Django model:

.. code-block:: python

    # models.py
    from django.db import models


    class MyModel(models.Model):
        # ...

        graphql_interfaces = (CustomInterface,)


or a ``StreamField`` block:

.. code-block:: python

    # blocks.py
    from wagtail.core import blocks


    class MyStructBlock(blocks.StructBlock):
        # ...

        graphql_interfaces = (CustomInterface,)

The provided interfaces will be added to the base interfaces for the model.
