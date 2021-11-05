Examples
========

Basic Demo
^^^^^^^^^^

Grapple works by iterating over all the models in your project and if it detects
a ``graphql_fields`` field then it builds a GraphQL type based on the structure
defined in the list.

Here is a GraphQL model configuration for the default page from the
Wagtail docs:

.. code-block:: python

    from grapple.models import (
        GraphQLString,
        GraphQLStreamfield,
    )


    class BlogPage(Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        body = StreamField(
            [
                ("heading", blocks.CharBlock(classname="full title")),
                ("paragraph", blocks.RichTextBlock()),
                ("image", ImageChooserBlock()),
            ]
        )

        content_panels = Page.content_panels + [
            FieldPanel("author"),
            FieldPanel("date"),
            StreamFieldPanel("body"),
        ]

        # Note these fields below:
        graphql_fields = [
            GraphQLString("heading"),
            GraphQLString("date"),
            GraphQLString("author"),
            GraphQLStreamfield("body"),
        ]

The following field can then be queries at http://localhost:8000/graphql using
something like:

::

    {
        pages {
            ...on BlogPage {
                heading
                date
                author
                body {
                    rawValue
                    ...on ImageChooserBlock {
                        image {
                            src
                        }
                    }
                }
            }
        }
    }


**Next Steps**

  * :doc:`../general-usage/graphql-types`
  * :doc:`../general-usage/preview`
