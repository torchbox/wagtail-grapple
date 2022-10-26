import graphene
from django.apps import apps

from .registry import registry


# Classes used to define what the Django field should look like in the GQL type
class GraphQLField:
    field_name: str
    field_type: str
    field_source: str

    def __init__(
        self, field_name: str, field_type: type = None, required: bool = None, **kwargs
    ):
        # Initiate and get specific field info.
        self.field_name = field_name
        self.field_type = field_type
        self.field_source = kwargs.get("source", field_name)

        # Add support for NonNull/required fields
        if required:
            self.field_type = graphene.NonNull(field_type)

        # Legacy collection API (Allow lists):
        self.extract_key = kwargs.get("key", None)
        is_list = kwargs.get("is_list", False)
        if is_list:
            self.field_type = graphene.List(field_type)


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

        # Create the nested type and wrap it in some list field.
        graphql_type = nested_type(field_name, *args, required=item_required, **kwargs)
        collection_type = graphene.List

        if is_paginated_queryset:
            type_class = nested_type(field_name, *args)().field_type()
            collection_type = lambda nested_type: PaginatedQuerySet(  # noqa: E731
                nested_type, type_class, required=required
            )
            return graphql_type, collection_type

        # Add queryset filtering when necessary.
        if (
            is_queryset
            or nested_type == GraphQLForeignKey
            or nested_type == GraphQLSnippet
        ):
            collection_type = QuerySetList

        # Add support for NonNull/required to wrapper field
        required_collection_type = None
        if required:
            required_collection_type = (
                lambda nested_type: collection_type(  # noqa: E731
                    nested_type, required=True
                )
            )

        return graphql_type, required_collection_type or collection_type

    return Mixin


def GraphQLEmbed(field_name: str):
    def Mixin():
        from .types.streamfield import EmbedBlock

        return GraphQLField(field_name, EmbedBlock)

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
