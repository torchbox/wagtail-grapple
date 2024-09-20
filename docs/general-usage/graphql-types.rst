GraphQL Types
=============

Each of the field types in last chapter correspond to an outputted GraphQL
(or more specifically Graphene) type. Many are self-explanatory such as
``GraphQLString`` or ``GraphQLFloat``, but some have a sub-selection which we
detail below.

An existing understanding of GraphQL types will help here.


ImageObjectType
^^^^^^^^^^^^^^^

Any image-based field type (whether ``GraphQLImage`` or StreamField block) will
return a ``ImageObjectType``. Images can be queried via the ``images`` field on
the root query type like so:

::

    query {
        images {
            src
        }
    }


``ImageObjectType`` describes a Wagtail image and provides the following fields:

::

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
        preserveSvg: Boolean
    ): String
    isSvg: Boolean!



``ImageRenditionObjectType`` describes a Wagtail image rendition and provides the following fields:

::

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

::

    id: ID
    title: String
    file: String
    createdAt: DateTime
    fileSize: Int
    fileHash: String


SettingObjectType
^^^^^^^^^^^^^^^^^

Similar to ``SnippetObjectType``, Settings are grouped together under the
``SettingObjectType`` union. You can then query any settings that you have
appended a ``graphql_fields`` list to like so:

::

    query {
        settings {
            ...on SocialMediaSettings {
                facebook
                instagram
                youtube
            }
        }
    }

You can also query a setting by model name:

::

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

::

    id: ID
    port: Int
    siteName: String
    hostname: String
    isDefaultSite: Boolean
    rootPage: PageInterface
    page(id: Int, slug: String, urlPath: String, contentType: String, token: String): PageInterface
    pages(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]


The plural ``sites`` field can be queried like so:

::

    query {
        sites {
            port
            hostname
        }
    }

The singular ``site`` field accepts the following arguments:

::

    # Either the `id` or `hostname` must be provided.
    id: ID
    hostname: String

and can be queried like so:

::

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

::

    query {
        search(query:"blog") {
            ...on BlogPage {
                title
            }
        }
    }
