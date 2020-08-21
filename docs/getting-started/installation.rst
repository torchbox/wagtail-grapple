Installation
============

Add library to an existing Wagtail project:

``pip install wagtail_grapple``

Add the following to the ``installed_apps`` list in your wagtail
settings file:

::

   installed_apps = [
       ...
       "grapple",
       "graphene_django",
       ...
   ]

For GraphQL Subscriptions with Django Channels, run ``pip install wagtail_grapple[channels]`` and add
``channels`` to installed apps:

::

   installed_apps = [
       ...
       "grapple",
       "graphene_django",
       "channels",
       ...
   ]

Add the following to the bottom of the same settings file where each key
is the app you want to this library to scan and the value is the prefix
you want to give to GraphQL types (you can usually leave this blank):

::

   # Grapple Config:
   GRAPHENE = {"SCHEMA": "grapple.schema.schema"}
   GRAPPLE_APPS = {
       "home": ""
   }

Add the GraphQL urls to your ``urls.py``:

::

   from grapple import urls as grapple_urls
   ...
   urlpatterns = [
       ...
       url(r"", include(grapple_urls)),
       ...
   ]

Done! Now you can proceed onto configuring your models to generate
GraphQL types that adopt their structure.

By default, all field and argument names will be converted from `snake_case`
to `camelCase`. To disable this behavior, set the `GRAPPLE_AUTO_CAMELCASE`
setting to `False` on your project settings.

* **Next Steps**

  * :doc:`examples`
  * :doc:`../general-usage/graphql-types`


*Your GraphQL endpoint is available at http://localhost:8000/graphql/*
