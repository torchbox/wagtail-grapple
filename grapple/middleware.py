from graphene import ResolveInfo
from graphql.execution.middleware import get_middleware_resolvers

from .registry import registry

ROOT_TYPES = ["Query", "Mutation", "Subscription"]


class IsAuthenticatedMiddleware(object):
    def resolve(self, next, root, info, **args):
        if not info.context.user.is_authenticated:
            return None
        return next(root, info, **args)


class IsAnonymousMiddleware(object):
    def resolve(self, next, root, info, **args):
        if not info.context.user.is_anonymous:
            return None
        return next(root, info, **args)


class GrappleMiddleware(object):
    def __init__(self):
        self.field_middlewares = {}
        for field_name in registry.field_middlewares:
            self.field_middlewares[field_name] = list(
                get_middleware_resolvers(registry.field_middlewares[field_name])
            )

    def resolve(self, next, root, info: ResolveInfo, **args):
        field_name = info.field_name
        parent_name = info.parent_type.name
        if field_name in self.field_middlewares and parent_name in ROOT_TYPES:
            for middleware in self.field_middlewares[field_name]:
                return middleware(next, root, info, **args)

        return next(root, info, **args)
