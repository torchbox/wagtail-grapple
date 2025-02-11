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

    from django.db import models
    from grapple.models import GraphQLRichText, GraphQLStreamfield, GraphQLString
    from wagtail import blocks
    from wagtail.models import Page
    from wagtail.images.blocks import ImageBlock
    from wagtail.fields import RichTextField, StreamField
    from wagtail.admin.edit_handlers import FieldPanel


    class BlogPage(Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        summary = RichTextField()
        body = StreamField(
            [
                ("heading", blocks.CharBlock(classname="full title")),
                ("paragraph", blocks.RichTextBlock()),
                ("image", ImageBlock()),
            ]
        )

        content_panels = Page.content_panels + [
            FieldPanel("author"),
            FieldPanel("date"),
            FieldPanel("summary"),
            FieldPanel("body"),
        ]

        # Note these fields below:
        graphql_fields = [
            GraphQLString("heading"),
            GraphQLString("date"),
            GraphQLString("author"),
            GraphQLRichText("summary"),
            GraphQLStreamfield("body"),
        ]

The following field can then be queries at http://localhost:8000/graphql using
something like:

::

    query {
        pages {
            ...on BlogPage {
                heading
                date
                author
                summary
                body {
                    rawValue
                    ...on ImageBlock {
                        image {
                            src
                        }
                        decorative
                        altText
                    }
                }
            }
        }
    }


**Next Steps**

  * :doc:`settings`
  * :doc:`../general-usage/graphql-types`
  * :doc:`../general-usage/preview`
