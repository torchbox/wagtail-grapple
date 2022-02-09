Headless Preview
================

Grapple also provides support for headless previews using the `Wagtail Headless Preview
<https://github.com/torchbox/wagtail-headless-preview>`_ package.
This means you can pass a unique 'preview token' to the GraphQL endpoint and preview a page as you update
it in the admin (in real-time!).

Grapple's Headless Preview is built-on GraphQL Subscriptions which means
that your client subscribes to the preview page and any changes in the Admin
will be pushed to your client via WebSockets. This allows you to add preview
support to any client whether that be a SPA or Native App.

Setup
^^^^^

See :ref:`usage with subscriptions<usage-with-subscriptions>` first to make sure you installed Django Channels when you installed Grapple.
Your installed apps in your settings should look like so:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "grapple",
        "graphene_django",
        "channels",
        "wagtail_headless_preview",
        # ...
    ]

Now you need to run the migrations that come with Wagtail Headless Preview.

::

   $ python manage.py migrate



You also want to add to your settings the URL you want to redirect to when the
user clicks the 'Preview' button:

.. code-block:: python

    HEADLESS_PREVIEW_CLIENT_URLS = {
        "default": "http://localhost:8001/preview",
    }

    HEADLESS_PREVIEW_LIVE = True

Two HTTP params are also passed to this url:
 - ``content_type``: The content type string of the Model you're viewing.
 - ``token``: The preview token you need to retrieve the preview data.

*Attention*: When the user clicks the "Preview" or "View Draft" button in the Wagtail admin the preview opens in a new tab. The URL in the preview tab will not reveal the actual preview URL set in the setting. It will rather show the admin URL of the page with an additional URL element ``/preview`` or ``/view_draft`` (e.g. ``http://localhost:8000/admin/pages/5/edit/preview/``).


Your next step is to subclass any Page models you want headless preview on with
``wagtail_headless_preview.models.HeadlessPreviewMixin`` to override the original Wagtail preview methods:

.. code-block:: python

    from wagtail_headless_preview.models import HeadlessPreviewMixin


    class BlogPage(HeadlessPreviewMixin, Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        advert = models.ForeignKey(
            "home.Advert",
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name="+",
        )


And you are done!


How to use
^^^^^^^^^^

Now when you click the 'Preview' button in Wagtail a page will open with the content of
your defined `HEADLESS_PREVIEW_CLIENT_URLS`. You can either load the preview token through
the HTTP params or through the ``used-token`` cookie which has been set in
both the Admin and the redirected page.

Once you've pushed the 'Preview' button, Any data input into the Admin form
will be pushed to your subscribed client. Pushing the button again will start
a new session with a new token.

To access the preview data you can use one of the three queries (the 'subscription'
declaration is optional if you want to do a one time query):

::

    subscription {
        page(contentType: "home.blogpage", token: "id=4:1hg5FZ:bPmOihaRCLGbo4mzZagvrJAqNWM") {
            title
        }
    }


::

    subscription {
        page(slug: "example-blog-page", token: "id=4:1hg5FZ:bPmOihaRCLGbo4mzZagvrJAqNWM") {
            title
        }
    }


::

    subscription {
        page(id: 1, token: "id=4:1hg5FZ:bPmOihaRCLGbo4mzZagvrJAqNWM") {
            title
        }
    }
