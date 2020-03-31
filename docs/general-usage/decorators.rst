Decorators
==========

Here are some useful decorators that allow you to expand your GraphQL schema further

@register_query_field
---------------------
.. module:: grapple.helpers
.. class:: register_query_field(field_name, query_fields)
Grapple exposes a few fields on the root schema such as ``pages``, ``images`` and ``redirects``. You can easily
expose a django model in your codebase by adding the ``@register_query_field`` decorator like so:

::
    from grapple.helpers import register_query_field

    @register_query_field('advert')
    class Advert(models.Model):
        url = models.URLField(null=True, blank=True)
        text = models.CharField(max_length=255)

        panels = [FieldPanel("url"), FieldPanel("text")]

        graphql_fields = [GraphQLString("url"), GraphQLString("text")]

        def __str__(self):
            return self.text


You can now query your adverts with the following query:

::

    {
        # Get all adverts
        adverts {
            url
            text
        }

        # Get a specific advert
        advert(id: 1) {
            url
            text
        }
    }

You can add custom query paramaters like so:

::

    @register_query_field('advert', {
        id: graphene.Int()
        url: graphene.String()
    })

and then use it in your queries:

::

    {
        # Get a specific advert
        advert(url: "some-unique-url") {
            url
            text
        }
    }
