GraphQL Types
=============

Each of the field types in last chapter correspond to an outputted GraphQL
(or more specifically Graphene) type. Many are self-explanatory such as
``GraphQLString`` or ``GraphQLFloat``, but some have a sub-selection which we
detail below.

An existing understanding of GraphQL types will help here.


PageInterface
^^^^^^^^^^^^^

The default GraphQL interface for all Wagtail Page-derived models.

This is accessible through the ``pages`` or ``page`` field on the root query type.

The interface exposes the following fields, following the Wagtail Page model fields and properties:

.. code-block:: graphql

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

.. code-block:: graphql

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

.. code-block:: graphql

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

.. code-block:: graphql

    id: ID                        # Can be used on it's own
    slug: String                  # Can be used on it's own
    urlPath: String               # Can be used on it's own
    token: String                 # Must be used with one of the others. Usually contentType
    contentType: String           # Can be used on it's own
    inSite: Boolean               # Can be used on it's own



ImageObjectType
^^^^^^^^^^^^^^^

Any image-based field type (whether ``GraphQLImage`` or StreamField block) will
return a ``ImageObjectType``. Images can be queried via the ``images`` field on
the root query type like so:

.. code-block:: graphql

    query {
        images {
            src
        }
    }


``ImageObjectType`` describes a Wagtail image and provides the following fields:

.. code-block:: graphql

    id: ID!
    collection: CollectionObjectType!
    title: String!
    file: String!
    width: Int!
    height: Int!
    createdAt: DateTime!
    focalPointX: Int
    focalPointY: Int
    focalPointWidth: Int
    focalPointHeight: Int
    fileSize: Int
    fileHash: String!
    url: String!
    aspectRatio: Float!
    sizes: String!
    tags: [TagObjectType!]!
    rendition(
        max: String
        min: String
        width: Int
        height: Int
        fill: String
        format: String
        bgcolor: String
        jpegquality: Int
        webpquality: Int
        preserveSvg: Boolean
    ): ImageRenditionObjectType
    srcSet(
        sizes: [Int]
        format: String
    ): String
    isSvg: Boolean!



``ImageRenditionObjectType`` describes a Wagtail image rendition and provides the following fields:

.. code-block:: graphql

    id: ID!
    filter_spec = String!
    file: String!
    width: Int!
    height: Int!
    focal_point_key = String!
    image: ImageObjectType!
    focalPoint: String
    url: String!
    alt = String!
    backgroundPositionStyle = String!


DocumentObjectType
^^^^^^^^^^^^^^^^^^

Very similar to ``ImageObjectType``; Is returned when using ``GraphQLDocument``
or by a StreamField block.

The following fields are returned:

.. code-block:: graphql

    id: ID
    title: String
    file: String
    createdAt: DateTime
    fileSize: Int
    fileHash: String



SnippetObjectType
^^^^^^^^^^^^^^^^^

You won't see much of ``SnippetObjectType`` as it's only a Union type that
groups all your Snippet models together. You can query all the available snippets
under the ``snippets`` field under the root Query, The query is similar to
an interface but ``SnippetObjectType`` doesn't provide any fields itself.

When snippets are attached to Pages you interact with your generated type itself
as opposed to an interface or base type.

An example of querying all snippets:

.. code-block:: graphql

    query {
        snippets {
            ...on Advert {
                id
                url
                text
            }
        }
    }


SettingObjectType
^^^^^^^^^^^^^^^^^

Similar to ``SnippetObjectType``, Settings are grouped together under the
``SettingObjectType`` union. You can then query any settings that you have
appended a ``graphql_fields`` list to like so:

.. code-block:: graphql

    {
        settings {
            ...on SocialMediaSettings {
                facebook
                instagram
                youtube
            }
        }
    }

You can also query a setting by model name:

.. code-block:: graphql

    query {
        setting(name: "SocialMediaSettings") {
            ...on SocialMediaSettings {
                facebook
                instagram
                youtube
            }
        }
    }


SiteObjectType
^^^^^^^^^^^^^^

Field type based on the Wagtail's ``Site`` model. This is accessible through
the ``sites`` or ``site`` field on the root query type. Available fields for the
``SiteObjectType`` are:

.. code-block:: graphql

    id: ID
    port: Int
    siteName: String
    hostname: String
    isDefaultSite: Boolean
    rootPage: PageInterface
    page(id: Int, slug: String, urlPath: String, contentType: String, token: String): PageInterface
    pages(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]


The plural ``sites`` field can be queried like so:

.. code-block:: graphql

    query {
        sites {
            port
            hostname
        }
    }

The singular ``site`` field accepts the following arguments:

.. code-block:: graphql

    # Either the `id` or `hostname` must be provided.
    id: ID
    hostname: String

and can be queried like so:

.. code-block:: graphql

    query {
        site(hostname: "my.domain") {
            pages {
                title
            }
        }
    }


Search
^^^^^^

You can also simply search all models via GraphQL like so:

.. code-block:: graphql

    query {
        search(query:"blog") {
            ...on BlogPage {
                title
            }
        }
    }
