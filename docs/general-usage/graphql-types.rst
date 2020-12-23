GraphQL Types
=============

Each of the field types in last chapter correspond to an outputted GraphQL
(or more specifically Graphene) type. Many are self-explanatory such as
``GraphQLString`` or ``GraphQLFloat``, but some have a sub-selection which we
detail below.

An existing understanding of GraphQL types will help here.


PageInterface
^^^^^^^^^^^^^

One of the things you'll do most when using Grapple is querying pages and to
do that you'll have to use the ``PageInterface``. This is accessible through
the ``pages`` or ``page`` field on the root query type.



The interface itself has the following fields (you'll notice a similarity to
the fields on a Wagtail Page model). As such with GraphQL interfaces, your page
models inherit these fields also:

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


Also, each of your Page models that you have appended ``graphql_fields`` to will be
available here by using a 'on' spread operator and the name of the model like so:

::

    {
        pages {
            ...on BlogPage {
                title
            }
        }
    }


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
    contentType: String
    inSite: Boolean


The singular ``page`` field accepts the following arguments:

::

    id: Int                       # Can be used on it's own
    slug: String                  # Can be used on it's own
    urlPath: String               # Can be used on it's own
    token: String                 # Must be used with one of the others. Usually contentType
    contentType: String           # Can be used on it's own
    inSite: Boolean               # Can be used on it's own



ImageObjectType
^^^^^^^^^^^^^^^

Any image-based field type (whether ``GraphQLImage`` or Streamfield block) will
return a ``ImageObjectType``. Images are queryable from the ``images`` field on
the root query type like so:

::

    {
        images {
            src
        }
    }


``ImageObjectType`` provides the following fields which include all the fields
need for Gatsby Image features to work (see Handy Fragments page for more info):

::

    id: ID!
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
    renditions: [ImageRenditionObjectType]
    src: String
    srcSet(sizes: [Int]): String
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
    ): ImageRenditionObjectType


ImageRenditions are useful feature in Wagtail and they exist in Grapple as well
the ``ImageRenditionObjectType`` provides the following fields:

::

    id: ID
    filterSpec: String!
    file: String!
    width: Int
    height: Int
    focalPointKey: String!
    image: ImageObjectType!
    url: String


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



SnippetObjectType
^^^^^^^^^^^^^^^^^

You won't see much of ``SnippetObjectType`` as it's only a Union type that
groups all your Snippet models together. You can query all the available snippets
under the ``snippets`` field under the root Query, The query is similar to
an interface but ``SnippetObjectType`` doesn't provide any fields itself.

When snippets are attached to Pages you interact with your generated type itself
as opposed to an interface or base type.

An example of querying all snippets:

::

    {
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

::

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

::

    {
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
    page(id: Int, slug: String, urlPath: String, contentType: String, token: String, inSite: Boolean): PageInterface
    pages(limit: PositiveInt, offset: PositiveInt, order: String, searchQuery: String, id: ID): [PageInterface]


The plural ``sites`` field is queryable like so:

::

    {
        sites {
            port
            hostname
        }
    }

The singular ``site`` field accepts the following arguments:

::

    # Either the `id` or `hostName` must be provided.
    id: ID
    hostName: String

and is queryable like so:

::

    {
        site(hostName: "my.domain") {
            pages {
                title
            }
        }
    }


Search
^^^^^^

You can also simply search all models via GraphQL like so:

::

    {
        search(query:"blog") {
            ...on BlogPage {
                title
            }
        }
    }
