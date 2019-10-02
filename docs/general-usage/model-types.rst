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
.. class:: GraphQLString(field_name)

    A basic field type is string. Commonly used for CharField, TextField, 
    UrlField or any other Django field that returns a string as it's value.

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

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
.. class:: GraphQLCollection(nested_type, *args, **kwargs)

    A field type that wraps another model type in a list, Most likely to be used when referencing ForeignKey lists (like when using Orderables).

    .. attribute:: nested_type

        Pass another Grapple model type such as `GraphQLString` or `GraphQLForeignKey`.

    .. attribute:: *args

        Any args that you want to pass on to the nested type, you will always be passing `field_name` here for example.

    .. attribute:: **kwargs

        Any keyword args that you want to pass on to the nested type. 
        
        One keyword argument that is more powerful with Collections is the `source` argument. With ``GraphQLCollection``, 
        you can pass a source string that is multiple layers deep and Grapple will handle the querying for you through
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
.. class:: GraphQLInt(field_name)

    It's all fairly self explanatory but a `GraphQLInt` is used to 
    serialize interger based Django fields such as IntegerField 
    or PositiveSmallIntegerField.


GraphQLFloat
------------
.. module:: grapple.models
.. class:: GraphQLFloat(field_name)

    Like GraphQLInt, This field is used to serialize Float and Decimal fields.


GraphQLBoolean
--------------
.. module:: grapple.models
.. class:: GraphQLBoolean(field_name)


GraphQLStreamfield
------------------
.. module:: grapple.models
.. class:: GraphQLStreamfield(field_name)

This field type supports all built in Streamfield blocks. It also supports 
custom blocks built using StructBlock and the like.


GraphQLSnippet
--------------
.. module:: grapple.models
.. class:: GraphQLSnippet(field_name, snippet_modal)

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
.. class:: GraphQLForeignKey(field_name, content_type, is_list = False)

    GraphQLForeignKey is similar to GraphQLSnippet in that you pass a 
    ``field_name`` and ``content_type`` but you can also specify that the field
    is a list (for example when using ``Orderable``).

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: GraphQLString.snippet_modal

        String which defines the location of the snippet model you are referencing.

    .. attribute:: GraphQLString.is_list
    
        Define whether this field should be a list (for example when using ``Orderable``).

        .. warning:: ``is_list`` is now deprecated, please use ``GraphQLCollection`` field.

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
.. class:: GraphQLImage(field_name)

    To serialize the WagtailImages or custom Image model then use this field
    type.


GraphQLDocument
---------------

.. module:: grapple.models
.. class:: GraphQLDocument(field_name)

    To serialize the WagtailDocuments or custom Document model then use this 
    field type.
    

GraphQLField
------------

.. module:: grapple.models
.. class:: GraphQLForeignKey(field_name, graphene_type)

    If you want to build your own (or use graphene's built-in types) then 
    ``GraphQLField`` is what you need.

    .. attribute:: GraphQLString.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: GraphQLString.graphene_type

        The graphene type that you want to use.
