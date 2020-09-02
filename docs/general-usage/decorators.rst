Decorators
==========

Grapple exposes a few fields for the root schema such as ``pages``, ``images``, ``documents``, ``media`` and ``redirects``.

Here are some useful decorators that allow you to expand your GraphQL schema further:

@register_query_field
---------------------
.. module:: grapple.helpers
.. class:: register_query_field(field_name, plural_field_name=None, query_params=None, required=False, plural_required=False, plural_item_required=False)
You can easily expose any Django model from your codebase by adding the ``@register_query_field`` decorator like so:

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

You can add custom query parameters like so:

::

    @register_query_field('advert', 'adverts', {
        "id": graphene.Int()
        "url": graphene.String()
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

You can make the singular query return type required like so:

::

    @register_query_field('advert', required=True)

and then should look like this on your schema:

::

    advert(id: Int): Advert!

instead of:

::

    advert(id: Int): Advert

You can can also make the plural query return list type required:

::

    @register_query_field('advert', plural_required=True)

making the plural query look like this on your schema:

::

    adverts(id: Int, ...): [Advert]!

instead of the default:

::

    adverts(id: Int, ...): [Advert]

If you want to make the plural query return list item type required:

::

    @register_query_field('advert', plural_item_required=True)

making the plural query look like this:

::

    adverts(id: Int, ...): [Advert!]

instead of the default:

::

    adverts(id: Int, ...): [Advert]


@register_paginated_query_field
-------------------------------
.. module:: grapple.helpers
.. class:: register_paginated_query_field(field_name, plural_field_name=None, query_params=None, required=False, plural_required=False, plural_item_required=False)
You can easily expose any Django model from your codebase by adding the ``@register_paginated_query_field`` decorator like so:

::

    from grapple.helpers import register_paginated_query_field

    @register_paginated_query_field('advert')
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
        # Get adverts paginated
        adverts(page: 1, perPage: 10) {
            items {
                url
                text
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

        # Get a specific advert
        advert(id: 1) {
            url
            text
        }
    }

You can add custom query parameters like so:

::

    @register_paginated_query_field('advert', 'adverts', {
        "id": graphene.Int()
        "url": graphene.String()
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

You can make the singular query return type required like so:

::

    @register_paginated_query_field('advert', required=True)

and then should look like this on your schema:

::

    advert(id: Int): Advert!

instead of:

::

    advert(id: Int): Advert

You can can also make the plural query return list type required:

::

    @register_paginated_query_field('advert', plural_required=True)

making the plural query look like this on your schema:

::

    adverts(page: Int, perPage: Int, ...): AdvertPaginatedType!

    Type AdvertPaginatedType {
        items: [Advert]!
        pagination: PaginationType!
    }

instead of the default:

::

    adverts(page: Int, perPage: Int, ...): AdvertPaginatedType

    Type AdvertPaginatedType {
        items: [Advert]
        pagination: PaginationType
    }

If you want to make the plural query return list item type required:

::

    @register_paginated_query_field('advert', plural_item_required=True)

making the plural query look like this:

::

    adverts(page: Int, perPage: Int, ...): AdvertPaginatedType

    Type AdvertPaginatedType {
        items: [Advert!]
        pagination: PaginationType
    }

instead of the default:

::

    adverts(page: Int, perPage: Int, ...): AdvertPaginatedType

    Type AdvertPaginatedType {
        items: [Advert]
        pagination: PaginationType
    }
