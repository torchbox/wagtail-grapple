import graphene
import inspect
from typing import Type
from types import MethodType

from wagtail.core.models import Page

from graphene_django.types import DjangoObjectType

from .registry import registry
from .types.streamfield import StreamFieldInterface


streamfield_types = []


def register_streamfield_block(cls):
    from wagtail.core import blocks

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


def register_query_field(field_name, plural_field_name=None, query_params=None):
    from .types.structures import QuerySetList
    from .utils import resolve_queryset

    if not plural_field_name:
        plural_field_name = field_name + "s"

    def inner(cls):
        field_type = lambda: registry.models[cls]
        field_query_params = query_params or {"id": graphene.Int()}

        def Mixin():
            # Generic methods to get all and query one model instance.
            def resolve_singular(self, _, info, **kwargs):
                # If no filters then return nothing,
                if not kwargs:
                    return None

                try:
                    # If is a Page then only query live/public pages.
                    if issubclass(cls, Page):
                        return cls.objects.live().public().get(**kwargs)

                    return cls.objects.get(**kwargs)
                except:
                    return None

            def resolve_plural(self, _, info, **kwargs):
                qs = cls.objects
                if issubclass(cls, Page):
                    qs = cls.objects.live().public().order_by("-first_published_at")

                return resolve_queryset(qs.all(), info, **kwargs)

            # Create schema and add resolve methods
            schema = type(cls.__name__ + "Query", (), {})
            setattr(
                schema, field_name, graphene.Field(field_type, **field_query_params)
            )
            setattr(schema, plural_field_name, QuerySetList(field_type))
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

    return inner
