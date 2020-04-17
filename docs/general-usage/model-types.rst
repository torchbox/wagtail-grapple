Model Types
===========
What do we mean when we say types? Well in a Grapple context, a type is descriptor
function that tells grapple what type a Django Models field is represented by
in GraphQL.

The field types below are simple to use and all work in the same way.
We have created a bunch of built-in types for you to use in but you can always
create your own using [Graphene](https://github.com/graphql-python/graphene)
(Grapples underlying library) and take advantage of Grapple's generic ``GraphQLField`` type.


GraphQLString
-------------
.. module:: grapple.models
.. class:: GraphQLString(field_name, required=False)

    A basic field type is string. Commonly used for CharField, TextField,
    UrlField or any other Django field that returns a string as it's value.

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: GraphQLString.required

        Represents the field as non-nullable in the schema, This promises the client that it will have a value returned.

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
-------------
.. module:: grapple.models
.. class:: GraphQLCollection(nested_type, *args, required=False, item_required=False, **kwargs)

    A field type that wraps another model type in a list. Best suited for referencing Orderables (i.e. ForeignKey lists).

    .. attribute:: nested_type

        A Grapple model type such as `GraphQLString` or `GraphQLForeignKey`.

    .. attribute:: field_name

        The name of the class property used in your model definition.

    .. attribute:: *args

        Any positional arguments that you want to pass on to the nested type.

    .. attribute:: GraphQLString.required

        Represents the list as non-nullable in the schema, This promises the client that it will have an array will be returned.

    .. attribute:: GraphQLString.item_required

        Represents the fields in the list as non-nullable in the schema, This promises the client that it will have an array will be returned items that won't be null.

    .. attribute:: **kwargs

        Any keyword args that you want to pass on to the nested type.

        One keyword argument that is more powerful with Collections is the `source` argument. With ``GraphQLCollection``,
        You can pass a source string that is multiple layers deep and Grapple will handle the querying for you through
        multiple models (example below).

    In your models.py:
    ::

        from grapple.types import GraphQLString

        class BlogPage(Page):
            author = models.CharField(max_length=255)

            graphql_fields = [
                # Basic reference to Orderable model
                GraphQLCollection(
                    GraphQLForeignKey,
                    "related_links",
                    "home.blogpagerelatedlink"
                ),

                # Will return an array of just the url from each link
                GraphQLCollection(
                    GraphQLString,
                    "related_urls",
                    source="related_links.url"
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
            }
        }


GraphQLInt
----------
.. module:: grapple.models
.. class:: GraphQLInt(field_name, required=False)

    It's all fairly self explanatory but a `GraphQLInt` is used to
    serialize integer based Django fields such as IntegerField
    or PositiveSmallIntegerField.


GraphQLFloat
------------
.. module:: grapple.models
.. class:: GraphQLFloat(field_name, required=False)

    Like GraphQLInt, This field is used to serialize Float and Decimal fields.


GraphQLBoolean
--------------
.. module:: grapple.models
.. class:: GraphQLBoolean(field_name, required=False)


GraphQLStreamfield
------------------
.. module:: grapple.models
.. class:: GraphQLStreamfield(field_name, required=False)

This field type supports all built in Streamfield blocks. It also supports
custom blocks built using StructBlock and the like.


GraphQLSnippet
--------------
.. module:: grapple.models
.. class:: GraphQLSnippet(field_name, snippet_modal, required=False)

    GraphQLSnippet is a little bit more complicated; You first need to define
    a `graphql_field` list on your snippet like you do your page. Then you need
    to reference the snippet in the field type function.

    Your snippet values are then available through a sub-selection query on the
    field name.

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: GraphQLString.snippet_modal

        String which defines the location of the snippet model.


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

    GraphQLForeignKey is similar to GraphQLSnippet in that you pass a
    ``field_name`` and ``content_type`` but you can also specify that the field
    is a list (for example when using ``Orderable``).

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: GraphQLString.field_type

        String which defines the location of the model model you are referencing. You can also pass the model class itself.

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

    To serialize the WagtailImages or custom Image model then use this field
    type.


GraphQLDocument
---------------

.. module:: grapple.models
.. class:: GraphQLDocument(field_name, required=False)

    To serialize the WagtailDocuments or custom Document model then use this
    field type.


