Model Types
===========
What do we mean when we say types? In a Grapple context, a type is a descriptor
function that instructs Grapple what type a Django model field is represented by
in GraphQL.

The field types below are simple to use and all work in the same way.
We created a number of built-in types for general use, but you can create your own
using `Graphene <https://github.com/graphql-python/graphene/>`_ (Grapple's underlying library)
and take advantage of Grapple's generic ``GraphQLField`` type.


GraphQLString
-------------
.. module:: grapple.models
.. class:: GraphQLString(field_name, required=False)

    A basic field type is string. Commonly used for CharField, TextField,
    UrlField or any other Django field that returns a string as it's value.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.

    In your models.py:
    ::

        from grapple.types import GraphQLString

        class BlogPage(Page):
            author = models.CharField(max_length=255)

            graphql_fields = [
                GraphQLString("author"),
            ]


    Example query:
    ::

        {
            page(slug: "example-blog-page") {
                author
            }
        }


GraphQLCollection
-----------------
.. module:: grapple.models
.. class:: GraphQLCollection(nested_type, field_name, *args, is_queryset=False, is_paginated_queryset=False, required=False, item_required=False, **kwargs)

    A field type that wraps another model type in a list. Best suited for referencing Orderables (i.e. ForeignKey lists).

    .. attribute:: nested_type

        A Grapple model type such as ``GraphQLString`` or ``GraphQLForeignKey``.

    .. attribute:: field_name (str)

        The name of the class property used in your model definition.

    .. attribute:: *args

        Any positional arguments that you want to pass on to the nested type.

    .. attribute:: is_queryset (bool=False)

        This sets the arguments ``id``, ``limit``, ``offset``, ``search_query``, and ``order`` on the field.

    .. attribute:: is_paginated_queryset (bool=False)

        This sets the arguments ``id``, ``page``, ``per_page``, ``search_query``, and ``order`` on the field.

        Also sets the return value as an extended PaginatedType (example below).

    .. attribute:: required (bool=False)

        Represents the list as non-nullable in the schema. This promises the client that an array will be returned.

    .. attribute:: item_required (bool=False)

        Represents the fields in the list as non-nullable in the schema. This promises the client that the array items won't be null.

    .. attribute:: **kwargs

        Any keyword args that you want to pass on to the nested type.

        One keyword argument that is more powerful with Collections is the ``source`` argument. With ``GraphQLCollection``,
        You can pass a source string that is multiple layers deep and Grapple will handle the querying for you through
        multiple models (example below).

    In your models.py:
    ::

        from grapple.types import GraphQLString

        class BlogPage(Page):
            author = models.CharField(max_length=255)

            def paginated_related_links(self, info, **kwargs):
                return resolve_paginated_queryset(self.related_links.all(), info, **kwargs)

            graphql_fields = [
                # Basic reference to Orderable model
                GraphQLCollection(
                    GraphQLForeignKey,
                    "related_links",
                    "home.BlogPageRelatedLink"
                ),

                # Will return an array of just the url from each link
                GraphQLCollection(
                    GraphQLString,
                    "related_urls",
                    source="related_links.url"
                ),

                # Reference to Orderable model with pagination
                GraphQLCollection(
                    GraphQLForeignKey,
                    "paginated_related_links",
                    "home.BlogPageRelatedLink",
                    is_paginated_queryset=True
                ),
            ]


    Example query:
    ::

        {
            page(slug: "example-blog-page") {
                relatedUrls
                relatedLinks {
                    name
                }
                paginatedRelatedLinks {
                    items {
                        name
                    }
                    pagination {
                        total
                        count
                        perPage
                        currentPage
                        prevPage
                        nextPage
                        totalPages
                    }
                }
            }
        }


GraphQLInt
----------
.. module:: grapple.models
.. class:: GraphQLInt(field_name, required=False)

    Used to serialize integer-based Django fields such as ``IntegerField``
    or ``PositiveSmallIntegerField``.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


GraphQLFloat
------------
.. module:: grapple.models
.. class:: GraphQLFloat(field_name, required=False)

    Like ``GraphQLInt``, this field is used to serialize ``Float`` and ``Decimal`` fields.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


GraphQLBoolean
--------------
.. module:: grapple.models
.. class:: GraphQLBoolean(field_name, required=False)

    Used to serialize ``Boolean`` fields.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


GraphQLStreamfield
------------------
.. module:: grapple.models
.. class:: GraphQLStreamfield(field_name, required=False)

    This field type supports all built-in ``Streamfield`` blocks. It also supports
    custom blocks built using ``StructBlock`` and the like.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


GraphQLSnippet
--------------
.. module:: grapple.models
.. class:: GraphQLSnippet(field_name, snippet_model, required=False)

    ``GraphQLSnippet`` is a little bit more complicated; You first need to define
    a `graphql_field` list on your snippet like you do your page. Then you need
    to reference the snippet in the field type function.

    Your snippet values are then available through a sub-selection query on the
    field name.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: snippet_model (str)

        String which defines the location of the snippet model.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


    In your models.py:

    ::

        class BookPage(Page):
            advert = models.ForeignKey(
                'demo.Advert',
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='+'
            )

            graphql_fields = [
                GraphQLSnippet('advert', 'demo.Advert'),
            ]

            content_panels = Page.content_panels + [
                SnippetChooserPanel('advert'),
            ]

        @register_snippet
        class Advert(models.Model):
            url = models.URLField(null=True, blank=True)
            text = models.CharField(max_length=255)

            graphql_fields = [
                GraphQLString('url'),
                GraphQLString('text'),
            ]

            panels = [
                FieldPanel('url'),
                FieldPanel('text'),
            ]

            def __str__(self):
                return self.text


    ::

        #Example Query
        {
            page(slug: "some-blog-page") {
                advert {
                    url
                    text
                }
            }
        }


GraphQLForeignKey
-----------------
.. module:: grapple.models
.. class:: GraphQLForeignKey(field_name, content_type, required=False)

    ``GraphQLForeignKey`` is similar to ``GraphQLSnippet`` in that you pass a
    ``field_name`` and ``content_type`` but you can also specify that the field
    is a list (for example when using ``Orderable``).

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: content_type (str)

        String which defines the location of the model model you are referencing. You can also pass the model class itself.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.

    ::

        class BookPage(Page):
            advert = models.ForeignKey(
                'demo.Advert',
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='+'
            )

            graphql_fields = [
                GraphQLSnippet('advert', 'demo.Advert'),
            ]

            content_panels = Page.content_panels + [
                SnippetChooserPanel('advert'),
            ]


GraphQLImage
------------

.. module:: grapple.models
.. class:: GraphQLImage(field_name, required=False)

    Use this field type to serialize the core Wagtail or your custom Image model.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.


GraphQLDocument
---------------

.. module:: grapple.models
.. class:: GraphQLDocument(field_name, required=False)

    Use this field type to serialize the core Wagtail or your custom Document model.

    .. attribute:: field_name (str)

        This is the name of the class property used in your model definition.

    .. attribute:: required (bool=False)

        Represents the field as non-nullable in the schema. This promises the client that it will have a value returned.
