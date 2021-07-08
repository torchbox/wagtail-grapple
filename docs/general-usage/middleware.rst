Middleware
==========

You can use ``middleware`` to affect the evaluation of fields in your schema.

A middleware is any object or function that responds to ``resolve(next_middleware, *args).``

Inside that method, it should either:

    - Send ``resolve`` to the next middleware to continue the evaluation; or
    - Return a value to end the evaluation early.


Resolve arguments
-----------------

Middlewares ``resolve`` is invoked with several arguments:

- ``next`` represents the execution chain. Call ``next`` to continue evaluation.
- ``root`` is the root value object passed throughout the query.
- ``info`` is the resolver info.
- ``args`` is the dict of arguments passed to the field.


GrappleMiddleware
-----------------
.. module:: grapple.middleware
.. class:: GrappleMiddleware(object)

::

    GRAPHENE = {
        # ...
        'MIDDLEWARE': 'grapple.middleware.GrappleMiddleware',
    }


Examples
--------


Authenticated Middleware
^^^^^^^^^^^^^^^^^^^^^^^^
.. module:: grapple.middleware
.. class:: IsAuthenticatedMiddleware(object)

This middleware only continues evaluation if the request is authenticated.

::

    class IsAuthenticatedMiddleware(object):
        def resolve(self, next, root, info, **args):
            if not info.context.user.is_authenticated:
                return None
            return next(root, info, **args)


Anonymous Middleware
^^^^^^^^^^^^^^^^^^^^
.. module:: grapple.middleware
.. class:: IsAnonymousMiddleware(object)

This middleware only continues evaluation if the request is **not** authenticated.

::

    class IsAnonymousMiddleware(object):
        def resolve(self, next, root, info, **args):
            if not info.context.user.is_anonymous:
                return None
            return next(root, info, **args)
