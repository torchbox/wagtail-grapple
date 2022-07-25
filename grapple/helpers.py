import inspect
from types import MethodType

import graphene
from django.utils.translation import gettext_lazy as _
from graphene.utils.str_converters import to_camel_case
from wagtail.core.models import Page

from .registry import registry
from .settings import grapple_settings
from .types.streamfield import StreamFieldInterface

streamfield_types = []
field_middlewares = {}


def register_streamfield_block(cls):
    base_block = None
    for block_class in inspect.getmro(cls):
        if block_class in registry.streamfield_blocks:
            base_block = registry.streamfield_blocks[block_class]

    streamfield_types.append(
        {
            "cls": cls,
            "type_prefix": "",
            "interface": StreamFieldInterface,
            "base_type": base_block,
        }
    )

    return cls


def register_graphql_schema(schema_cls):
    registry.schema.append(schema_cls)
    return schema_cls


def register_field_middleware(field_name: str, middleware):
    assert isinstance(middleware, list), "middleware should be list but got {}.".format(
        type(middleware)
    )
    if grapple_settings.AUTO_CAMELCASE:
        field_name = to_camel_case(field_name)

    if field_name in field_middlewares:
        field_middlewares[field_name] += middleware
    else:
        field_middlewares[field_name] = middleware


def register_query_field(
    field_name,
    plural_field_name=None,
    query_params=None,
    required=False,
    plural_required=False,
    plural_item_required=False,
    middleware=None,
):
    from .types.structures import QuerySetList
    from .utils import resolve_queryset

    if not plural_field_name:
        plural_field_name = field_name + "s"

    def inner(cls):
        field_type = lambda: registry.models[cls]  # noqa: E731
        field_query_params = query_params
        if field_query_params is None:
            field_query_params = {"id": graphene.Int()}

            if issubclass(cls, Page):
                field_query_params["slug"] = graphene.Argument(
                    graphene.String, description=_("The page slug.")
                )
                field_query_params["url_path"] = graphene.Argument(
                    graphene.String, description=_("The url path.")
                )
                field_query_params["token"] = graphene.Argument(
                    graphene.String, description=_("The preview token.")
                )

        def Mixin():
            # Generic methods to get all and query one model instance.
            def resolve_singular(self, _, info, **kwargs):
                # If no filters then return nothing,
                if not kwargs:
                    return None

                try:
                    # If is a Page then only query live/public pages.
                    if issubclass(cls, Page):
                        if "token" in kwargs and hasattr(
                            cls, "get_page_from_preview_token"
                        ):
                            return cls.get_page_from_preview_token(kwargs.get("token"))

                        qs = cls.objects.live().public()
                        url_path = kwargs.pop("url_path", None)
                        if url_path:
                            if not url_path.endswith("/"):
                                url_path += "/"
                            return qs.filter(
                                url_path__endswith=url_path, **kwargs
                            ).first()

                        return qs.get(**kwargs)

                    return cls.objects.get(**kwargs)
                except (cls.DoesNotExist, cls.MultipleObjectsReturned):
                    return None

            def resolve_plural(self, _, info, **kwargs):
                qs = cls.objects
                if issubclass(cls, Page):
                    qs = qs.live().public()
                    if "order" not in kwargs:
                        kwargs["order"] = "-first_published_at"

                return resolve_queryset(qs.all(), info, **kwargs)

            # Create schema and add resolve methods
            schema = type(cls.__name__ + "Query", (), {})

            singular_field_type = field_type
            if required:
                singular_field_type = graphene.NonNull(field_type)

            setattr(
                schema,
                field_name,
                graphene.Field(singular_field_type, **field_query_params),
            )

            plural_field_type = field_type
            if plural_item_required:
                plural_field_type = graphene.NonNull(field_type)

            setattr(
                schema,
                plural_field_name,
                QuerySetList(plural_field_type, required=plural_required),
            )

            setattr(
                schema, "resolve_" + field_name, MethodType(resolve_singular, schema)
            )
            setattr(
                schema,
                "resolve_" + plural_field_name,
                MethodType(resolve_plural, schema),
            )
            return schema

        # Send schema to Grapple schema.
        register_graphql_schema(Mixin())
        return cls

    if middleware is not None:
        register_field_middleware(field_name, middleware)
        register_field_middleware(plural_field_name, middleware)

    return inner


def register_paginated_query_field(
    field_name,
    plural_field_name=None,
    query_params=None,
    required=False,
    plural_required=False,
    plural_item_required=False,
    middleware=None,
):
    from .types.structures import PaginatedQuerySet
    from .utils import resolve_paginated_queryset

    if not plural_field_name:
        plural_field_name = field_name + "s"

    def inner(cls):
        field_type = lambda: registry.models[cls]  # noqa: E731
        field_query_params = query_params
        if field_query_params is None:
            field_query_params = {"id": graphene.Int()}

            if issubclass(cls, Page):
                field_query_params["slug"] = graphene.Argument(
                    graphene.String, description=_("The page slug.")
                )
                field_query_params["url_path"] = graphene.Argument(
                    graphene.String, description=_("The page url path.")
                )
                field_query_params["token"] = graphene.Argument(
                    graphene.String, description=_("The preview token.")
                )

        def Mixin():
            # Generic methods to get all and query one model instance.
            def resolve_singular(self, _, info, **kwargs):
                # If no filters then return nothing.
                if not kwargs:
                    return None

                try:
                    # If is a Page then only query live/public pages.
                    if issubclass(cls, Page):
                        if "token" in kwargs and hasattr(
                            cls, "get_page_from_preview_token"
                        ):
                            return cls.get_page_from_preview_token(kwargs.get("token"))

                        qs = cls.objects.live().public()
                        url_path = kwargs.pop("url_path", None)
                        if url_path:
                            if not url_path.endswith("/"):
                                url_path += "/"
                            return qs.filter(
                                url_path__endswith=url_path, **kwargs
                            ).first()
                        return qs.get(**kwargs)

                    return cls.objects.get(**kwargs)
                except (cls.DoesNotExist, cls.MultipleObjectsReturned):
                    return None

            def resolve_plural(self, _, info, **kwargs):
                qs = cls.objects
                if issubclass(cls, Page):
                    qs = qs.live().public()
                    if "order" not in kwargs:
                        kwargs["order"] = "-first_published_at"

                return resolve_paginated_queryset(qs.all(), info, **kwargs)

            # Create schema and add resolve methods
            schema = type(cls.__name__ + "Query", (), {})

            singular_field_type = field_type
            if required:
                singular_field_type = graphene.NonNull(field_type)

            setattr(
                schema,
                field_name,
                graphene.Field(singular_field_type, **field_query_params),
            )

            plural_field_type = field_type
            if plural_item_required:
                plural_field_type = graphene.NonNull(field_type)

            setattr(
                schema,
                plural_field_name,
                PaginatedQuerySet(plural_field_type, cls, required=plural_required),
            )

            setattr(
                schema, "resolve_" + field_name, MethodType(resolve_singular, schema)
            )
            setattr(
                schema,
                "resolve_" + plural_field_name,
                MethodType(resolve_plural, schema),
            )
            return schema

        # Send schema to Grapple schema.
        register_graphql_schema(Mixin())
        return cls

    if middleware is not None:
        register_field_middleware(field_name, middleware)
        register_field_middleware(plural_field_name, middleware)

    return inner


def register_singular_query_field(
    field_name, query_params=None, required=False, middleware=None
):
    def inner(cls):
        field_type = lambda: registry.models[cls]  # noqa: E731
        field_query_params = query_params

        if field_query_params is None:
            field_query_params = {
                "order": graphene.Argument(
                    graphene.String,
                    description=_("Use the Django QuerySet order_by format."),
                ),
            }
            if issubclass(cls, Page):
                field_query_params["token"] = graphene.Argument(
                    graphene.String, description=_("The preview token.")
                )

        def Mixin():
            # Generic methods to get all and query one model instance.
            def resolve_singular(self, _, info, **kwargs):
                qs = cls.objects.all()
                if "order" in kwargs:
                    qs = qs.order_by(
                        *(x.strip() for x in kwargs.pop("order").split(","))
                    )

                # If is a Page then only query live/public pages.
                if issubclass(cls, Page):
                    if "token" in kwargs and hasattr(
                        cls, "get_page_from_preview_token"
                    ):
                        return cls.get_page_from_preview_token(kwargs.get("token"))

                    return qs.live().public().filter(**kwargs).first()

                return qs.filter(**kwargs).first()

            # Create schema and add resolve methods
            schema = type(cls.__name__ + "Query", (), {})

            singular_field_type = field_type
            if required:
                singular_field_type = graphene.NonNull(field_type)

            setattr(
                schema,
                field_name,
                graphene.Field(singular_field_type, **field_query_params),
            )

            setattr(
                schema, "resolve_" + field_name, MethodType(resolve_singular, schema)
            )
            return schema

        # Send schema to Grapple schema.
        register_graphql_schema(Mixin())
        return cls

    if middleware is not None:
        register_field_middleware(field_name, middleware)

    return inner
