import inspect

from graphene import ResolveInfo

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
    def resolve(self, next, root, info: ResolveInfo, **args):
        field_name = info.field_name
        parent_name = info.parent_type.name
        if field_name in registry.field_middlewares and parent_name in ROOT_TYPES:
            if not isinstance(registry.field_middlewares[field_name], list):
                return next(root, info, **args)

            for middleware in registry.field_middlewares[field_name]:
                if inspect.isfunction(middleware):
                    return middleware(next, root, info, **args)
                elif inspect.isclass(middleware):
                    return middleware().resolve(next, root, info, **args)
                else:
                    return next(root, info, **args)

        return next(root, info, **args)
