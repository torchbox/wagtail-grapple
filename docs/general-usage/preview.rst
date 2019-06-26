Headless Preview
================

Grapple also provides support for Headless Preview. This means you can pass a 
unique 'preview token' to the GraphQL endpoint and preview a page as you update
it in the admin (in real-time!).

Grapple's Headless Preview is built-on GraphQL Subscriptions which means
that your client subscribes to the preview page and any changes in the Admin
will be pushed to your client via WebSockets. This allows you to add preview 
support to any client whether that be a SPA or Native App.

Setup
^^^^^

Make sure you installed Django Channels (version 1) when you installed Grapple, 
your installed apps in your settings should look like so:

::

    INSTALLED_APPS = [
        ...
        "grapple",
        "graphene_django",
        "channels",
        ...
    ]


Add the following Django Channels configurarion to your settings. This tells 
Django Channels that you want to add a channel layer that points to Grapple
and you want to use the 'in-memory' backend. You will want to research different
Channel backends to see which one works best for your production enviroment:
https://channels.readthedocs.io/en/1.x/backends.html

::

    ASGI_APPLICATION = "asgi.channel_layer"
    CHANNELS_WS_PROTOCOLS = ["graphql-ws"]
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgiref.inmemory.ChannelLayer",
            "ROUTING": "grapple.urls.channel_routing",
        }
    }


You also want to add to your settings the URL you want to redirect to when the 
user clicks the 'Preview' button:

::

    GRAPPLE_PREVIEW_URL = "http://localhost:8001/preview"

Two HTTP params are also passed to this url:
 - content_type: The content type string of the Model you're viewing.
 - token: The preview token you need to retrieve the preview data.




You're next step is to subclass any Page models you want headless preview on with
`grapple.models.GrapplePageMixin` to  override the original Wagtail previewing methods:

::

    from grapple.models import GrapplePageMixin

    class BlogPage(GrapplePageMixin, Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        advert = models.ForeignKey(
            'home.Advert',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )


You're Done! Below is the how to use guide.


How to use
^^^^^^^^^^

Now when you click the 'Preview' button in Wagtail you will be redirected to 
your `GRAPPLE_PREVIEW_URL`. You can either load the preview token through
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