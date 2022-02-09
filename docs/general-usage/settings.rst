Settings
========

Configuration for Wagtail Grapple is all namespaced inside a single Django setting,
named ``GRAPPLE``.

For example your project's ``settings.py`` file might include something like this:

.. code-block:: python

    # settings.py
    GRAPPLE = {
        "APPS": ["home"],
        "ADD_SEARCH_HIT": True,
    }


Accessing settings
------------------

If you need to access the values of Wagtail Grapple's settings in your project, you should use the
``grapple_settings`` object. For example.

.. code-block:: python

    from grapple.settings import grapple_settings

    print(grapple_settings.APPS)

The ``grapple_settings`` object will check for any user-defined settings, and otherwise fall back to
the default values.


API Reference
-------------


Grapple settings
^^^^^^^^^^^^^^^^

APPS
****

A list/tuple of the apps that Grapple will scan for models to generate GraphQL types that adopt their structure.

Default: ``[]``


AUTO_CAMELCASE
**************

By default, all field and argument names will be converted from `snake_case` to `camelCase`.
To disable this behavior, set the ``GRAPPLE['AUTO_CAMELCASE']`` setting to `False`.

Default: ``True``


EXPOSE_GRAPHIQL
***************

By default, Grapple will add ``/graphql`` url to where you can make GET/POST GraphQL requests.
When setting ``GRAPPLE['EXPOSE_GRAPHIQL']`` to ``True``, the ``/graphiql`` url is also added to
provide access to GraphiQL.

Default: ``False``


Renditions settings
^^^^^^^^^^^^^^^^^^^

ALLOWED_IMAGE_FILTERS
*********************

To prevent arbitrary renditions from being generated, set ``GRAPPLE['ALLOWED_IMAGE_FILTERS']`` in
your settings to a `list` or `tuple` of allowed filters. Read more about generating renditions in the Wagtail docs
(`Generating renditions in Python <https://docs.wagtail.io/en/stable/advanced_topics/images/renditions.html#generating-renditions-in-python>`_ and
`How to use images in templates <https://docs.wagtail.io/en/stable/topics/images.html#how-to-use-images-in-templates>`_)

Default: ``None``

Example:

.. code-block:: python

    # settings.py
    GRAPPLE = {
        # ...
        "ALLOWED_IMAGE_FILTERS": [
            "width-1000",
            "fill-300x150|jpegquality-60",
            "width-700|format-webp",
        ]
    }

Note that the ``srcSet`` attribute on ``ImageObjectType`` generates ``width-*`` filters, so if in use
consider adding the relevant filters to the allowed list.


Search settings
^^^^^^^^^^^^^^^

ADD_SEARCH_HIT
**************

Setting this to ``True`` will log search queries so Wagtail can suggest promoted results.

Default: ``False``


Pagination settings
^^^^^^^^^^^^^^^^^^^

PAGE_SIZE
*********

Value used as default for both ``QuerySetList``' ``limit`` and ``PaginatedQuerySet``' ``perPage`` arguments.

Default: ``10``


MAX_PAGE_SIZE
*************

Value used to limit the maximum of items to be returned for both ``QuerySetList`` and ``PaginatedQuerySet`` types.

Default: ``100``
