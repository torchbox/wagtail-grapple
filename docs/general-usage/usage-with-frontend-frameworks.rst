Usage with frontend frameworks
##############################

A few features of Wagtail Grapple are useful for specific frontend frameworks.


Using Grapple with Gatsby
**************************

``wagtail-grapple`` provides a GraphQL API to Wagtail content that can be accessed by a wide range of consumers.

One common use case is to use Gatsby to fetch content from Wagtail, then build and deploy a static site built in React.

Frontend developers using Gatsby should check out `gatsby-source-wagtail <https://www.gatsbyjs.com/plugins/gatsby-source-wagtail/>`_, a plugin
designed to interface directly with ``wagtail-grapple`` to streamline queries to Wagtail.

.. _usage-with-nextjs:
Using Grapple with Next.js
***************************

``wagtail-grapple`` provides features that plays nicely with Next.js, see below for examples.

next/image
==========

The ``blurDataUrl`` field of ``<Image />`` component from Next.js can use the ``placeholderBlur`` field available on ``ImageObjectType``
