import graphene
import inspect
from typing import Type
from types import MethodType
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
