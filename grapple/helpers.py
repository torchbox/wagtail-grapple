import graphene
import inspect
from typing import Type
from graphene_django.types import DjangoObjectType

from .registry import registry
from .types.streamfield import StreamFieldInterface


def build_streamfield_type(
    cls: type,
    type_prefix: str,
    interface: graphene.Interface,
    base_type = graphene.ObjectType
):
    """
    Build a graphene node type from a model class and associate
    with an interface. If it has custom fields then implement them.
    """

    # Create a new blank node type
    class Meta:
        interfaces = (interface,) if interface is not None else tuple()
    
    type_name = type_prefix + cls.__name__
    type_meta = {"Meta": Meta}
    type_meta.update({"id": graphene.String()})

    # Add any custom fields to node if they are defined.
    if hasattr(cls, "graphql_fields"):
        for field in cls.graphql_fields:
            if callable(field):
                field = field()

            # Add field to GQL type with correct field-type
            if field.field_type is not None:
                type_meta[field.field_name] = field.field_type

    # Set excluded fields to stop errors cropping up from unsupported field
    # types.
    return type(type_name, (base_type,), type_meta)


def register_streamfield_block(cls):
    from wagtail.core import blocks

    base_block = None
    for block_class in inspect.getmro(cls):
        if block_class in registry.streamfield_blocks:
            base_block = registry.streamfield_blocks[block_class]

    registry.streamfield_blocks[cls] = build_streamfield_type(cls, '', StreamFieldInterface, base_block)
    
    return cls