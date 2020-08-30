.. Wagtail Grapple's documentation master file, created by
   sphinx-quickstart on Tue May 21 19:46:16 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Wagtail Grapple's documentation!
===========================================

There is a range of GraphQL packages for Python and specifically Django.
However, Getting these packages to work out of the box with an existing
infrastructure without errors isn't as easy to come by.

The purpose of Grapple is to be able to build GraphQL endpoints on a model
by model basis as quickly as possible. The setup and configuration have been
designed to be as simple but also provide the best features; No complex serializers
need to be written just add a ``graphql_fields`` list to your model and away
you go (although if you want to go deeper you can!).

Features
^^^^^^^^

-  Easily create GraphQL types by adding a small annotation in your
   models.
-  Supports traditional Wagtail models:

   -  Pages (including Streamfield & Orderables)
   -  Snippets
   -  Images
   -  Documents
   -  Media
   -  Settings
   -  Redirects
   -  Search (on all models)

-  Custom Image & Document model support
-  Pagination support
-  Advanced headless preview functionality built using GraphQL
   Subscriptions to enable Page previews on any device!


* **Getting Started**

  * :doc:`getting-started/installation`
  * :doc:`getting-started/examples`


* **General Usage**

  * :doc:`general-usage/model-types`
  * :doc:`general-usage/graphql-types`
  * :doc:`general-usage/preview`
  * :doc:`general-usage/decorators`


Contents
^^^^^^^^

.. toctree::
   :maxdepth: 2
   :titlesonly:

   getting-started/index
   general-usage/index
