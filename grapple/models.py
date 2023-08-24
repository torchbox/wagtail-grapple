from typing import Optional

import graphene

from django.apps import apps

from .exceptions import IllegalDeprecation
from .registry import registry


# Classes used to define what the Django field should look like in the GQL type
class GraphQLField:
    field_name: str
    field_type: Optional[type]
    field_source: Optional[str]
    description: Optional[str]
    deprecation_reason: Optional[str]

    def __init__(
        self, field_name: str, field_type: type = None, required: bool = None, **kwargs
    ):
        # Initiate and get specific field info.
        self.field_name = field_name
        self.field_type = field_type
        self.field_source = kwargs.get("source", field_name)
        self.description = kwargs.get("description", None)
        self.deprecation_reason = kwargs.get("deprecation_reason", None)

        # Add support for NonNull/required fields
        if required:
            if self.deprecation_reason is not None:
                raise IllegalDeprecation(
                    f"Field '{field_name}' cannot be both required and deprecated"
                )
            self.field_type = graphene.NonNull(field_type, description=self.description)

        # Legacy collection API (Allow lists):
        self.extract_key = kwargs.get("key", None)
        is_list = kwargs.get("is_list", False)
        if is_list:
            self.field_type = graphene.List(
                field_type,
                required=required,
                description=self.description,
                deprecation_reason=self.deprecation_reason,
            )


def GraphQLString(field_name: str, **kwargs):
    def Mixin():
        return GraphQLField(field_name, graphene.String, **kwargs)

    return Mixin


def GraphQLFloat(field_name: str, **kwargs):
    def Mixin():
        return GraphQLField(field_name, graphene.Float, **kwargs)

    return Mixin


def GraphQLInt(field_name: str, **kwargs):
    def Mixin():
        return GraphQLField(field_name, graphene.Int, **kwargs)

    return Mixin


def GraphQLBoolean(field_name: str, **kwargs):
    def Mixin():
        return GraphQLField(field_name, graphene.Boolean, **kwargs)

    return Mixin


def GraphQLSnippet(field_name: str, snippet_model: str, **kwargs):
    def Mixin():
        from django.apps import apps

        (app_label, model) = snippet_model.lower().split(".")
        mdl = apps.get_model(app_label, model)

        if mdl:
            field_type = lambda: registry.snippets[mdl]  # noqa: E731
        else:
            field_type = graphene.String

        return GraphQLField(field_name, field_type, **kwargs)

    return Mixin


def GraphQLForeignKey(field_name, content_type, is_list=False, **kwargs):
    def Mixin():
        field_type = None
        if isinstance(content_type, str):
            app_label, model = content_type.lower().split(".")
            mdl = apps.get_model(app_label, model)
            if mdl:
                field_type = lambda: registry.models.get(mdl)  # noqa: E731
        else:
            field_type = lambda: registry.models.get(content_type)  # noqa: E731

        return GraphQLField(field_name, field_type, **kwargs)

    return Mixin


def GraphQLStreamfield(field_name: str, **kwargs):
    def Mixin():
        from .types.streamfield import StreamFieldInterface

        # Note that GraphQLStreamfield children should always be considered list elements,
        # unless they specifically are requested not to. e.g. a GraphQLStreamfield for a nested StructBlock
        if "is_list" not in kwargs:
            kwargs["is_list"] = True
        return GraphQLField(field_name, StreamFieldInterface, **kwargs)

    return Mixin


def GraphQLRichText(field_name: str, **kwargs):
    def Mixin():
        from .types.rich_text import RichText

        return GraphQLField(field_name, RichText, **kwargs)

    return Mixin


def GraphQLImage(field_name: str, **kwargs):
    def Mixin():
        from .types.images import get_image_type

        return GraphQLField(field_name, get_image_type, **kwargs)

    return Mixin


def GraphQLDocument(field_name: str, **kwargs):
    def Mixin():
        from .types.documents import get_document_type

        return GraphQLField(field_name, get_document_type, **kwargs)

    return Mixin


def GraphQLPage(field_name: str, **kwargs):
    def Mixin():
        from .types.pages import PageInterface

        return GraphQLField(field_name, PageInterface, **kwargs)

    return Mixin


def GraphQLCollection(
    nested_type,
    field_name,
    *args,
    is_queryset=False,
    is_paginated_queryset=False,
    required=False,
    description=None,
    deprecation_reason=None,
    item_required=False,
    **kwargs,
):
    def Mixin():
        from .types.structures import PaginatedQuerySet, QuerySetList

        # Check if using nested field extraction:
        source = kwargs.get("source", None)
        if source and "." in source:
            source, *key = source.split(".")
            if key:
                kwargs["source"] = source
                kwargs["key"] = key

        if required and deprecation_reason is not None:
            raise IllegalDeprecation(
                f"Field '{field_name}' cannot be both required and deprecated"
            )

        # Create the nested type
        graphql_type = nested_type(field_name, *args, required=item_required, **kwargs)

        if is_paginated_queryset:
            # Wrap the nested type in a PaginatedQuerySet type
            type_class = nested_type(field_name, *args)().field_type()
            collection_type = lambda nested_type: PaginatedQuerySet(  # noqa: E731
                nested_type,
                type_class,
                required=required,
                description=description,
                deprecation_reason=deprecation_reason,
            )
            return graphql_type, collection_type

        # Add queryset filtering when necessary.
        if is_queryset or nested_type in (GraphQLForeignKey, GraphQLSnippet):
            # Wrap the nested type in a QuerySetList type
            collection_type = QuerySetList
        else:
            # Wrap the nested type in a List type
            collection_type = graphene.List

        # Add support for NonNull/required to wrapper field
        required_collection_type = None
        if required:

            def required_collection_type(nested_type):
                return collection_type(nested_type, required=True)

        return graphql_type, required_collection_type or collection_type

    return Mixin


def GraphQLEmbed(field_name: str, **kwargs):
    def Mixin():
        from .types.streamfield import EmbedBlock

        return GraphQLField(field_name, EmbedBlock, **kwargs)

    return Mixin


def GraphQLTag(field_name: str, **kwargs):
    def Mixin():
        from .types.tags import TagObjectType

        if "is_list" not in kwargs:
            kwargs["is_list"] = True
        return GraphQLField(field_name, TagObjectType, **kwargs)

    return Mixin


if apps.is_installed("wagtailmedia"):

    def GraphQLMedia(field_name: str, **kwargs):
        def Mixin():
            from .types.media import get_media_type

            return GraphQLField(field_name, get_media_type, **kwargs)

        return Mixin
