Installation
#############

Basic usage
===========

Add library to an existing Wagtail project:

``pip install wagtail_grapple``

Add the following to the ``INSTALLED_APPS`` list in your Wagtail
settings file:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "grapple",
        "graphene_django",
        # ...
    ]

Add the following to the bottom of the same settings file where each key
is the app you want to this library to scan and the value is the prefix
you want to give to GraphQL types (you can usually leave this blank):

.. code-block:: python

    # Grapple Config:
    GRAPHENE = {"SCHEMA": "grapple.schema.schema"}
    GRAPPLE = {
        "APPS": ["home"],
    }

Add the GraphQL urls to your ``urls.py``:

.. code-block:: python

    from grapple import urls as grapple_urls

    # ...
    urlpatterns = [
        # ...
        url(r"", include(grapple_urls)),
        # ...
    ]

Done! Now you can proceed onto configuring your models to generate
GraphQL types that adopt their structure.

By default, Grapple uses :doc:`these settings <../general-usage/settings>`.

* **Next Steps**

  * :doc:`examples`
  * :doc:`../general-usage/graphql-types`


*Your GraphQL endpoint is available at http://localhost:8000/graphql/*

 .. _usage-with-subscriptions:
Usage with subscriptions
========================

To enable GraphQL Subscriptions, you need to install Grapple with Django Channels.
Run ``pip install wagtail_grapple[channels]`` and add ``channels`` to installed apps:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "grapple",
        "graphene_django",
        "channels",
        # ...
    ]

Add the following Django Channels configuration to your settings.

.. code-block:: python

    ASGI_APPLICATION = "graphql_ws.django.routing.application"
