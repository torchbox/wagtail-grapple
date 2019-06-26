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
GraphQL types that adopt their stucture.

* **Next Steps**

  * :doc:`examples`
  * :doc:`../general-usage/types`


*Your graphql endpoint is available at http://localhost:8000/graphql/*
