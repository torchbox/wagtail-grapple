from functools import partial

from graphene import ResolveInfo
from graphql.execution.middleware import get_middleware_resolvers

from .registry import registry


ROOT_TYPES = ["Query", "Mutation", "Subscription"]


class IsAuthenticatedMiddleware:
    def resolve(self, next, root, info, **kwargs):
        if not info.context.user.is_authenticated:
            return None
        return next(root, info, **kwargs)


class IsAnonymousMiddleware:
    def resolve(self, next, root, info, **kwargs):
        if not info.context.user.is_anonymous:
            return None
        return next(root, info, **kwargs)


class GrappleMiddleware:
    def __init__(self):
        self.field_middlewares = {}
        for field_name in registry.field_middlewares:
            #  get_middleware_resolvers expects an instantiated class, if passing a class-based middleware.
            middlewares = tuple(
                middleware() if isinstance(middleware, type) else middleware
                for middleware in registry.field_middlewares[field_name]
            )
            self.field_middlewares[field_name] = list(
                get_middleware_resolvers(middlewares)
            )

    def resolve(self, next, root, info: ResolveInfo, **kwargs):
        field_name = info.field_name
        parent_name = info.parent_type.name
        if field_name in self.field_middlewares and parent_name in ROOT_TYPES:
            middlewares = self.field_middlewares[field_name].copy()
            while middlewares:
                next = partial(middlewares.pop(), next)

        return next(root, info, **kwargs)
