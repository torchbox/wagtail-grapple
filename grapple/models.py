import graphene
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .registry import registry


# Classes used to define what the Django field should look like in the GQL type
class GraphQLField:
    field_name: str
    field_type: str
    field_source: str

    def __init__(
        self, field_name: str, field_type: type = None, required=None, **kwargs
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


def GraphQLSnippet(
    field_name: str, snippet_model: str, is_list: bool = False, **kwargs
):
    def Mixin():
        from django.apps import apps

        (app_label, model) = snippet_model.lower().split(".")
        mdl = apps.get_model(app_label, model)

        if mdl:
            field_type = lambda: registry.snippets[mdl]
        else:
            field_type = graphene.String

        if field_type and is_list:
            field_type = graphene.List(field_type)

        return GraphQLField(field_name, field_type, **kwargs)

    return Mixin


def GraphQLForeignKey(field_name, content_type, is_list=False, **kwargs):
    def Mixin():
        field_type = None
        if isinstance(content_type, str):
            app_label, model = content_type.lower().split(".")
            mdl = apps.get_model(app_label, model)
            if mdl:
                field_type = lambda: registry.models.get(mdl)
        else:
            field_type = lambda: registry.models.get(content_type)

        return GraphQLField(field_name, field_type, **kwargs)

    return Mixin


def GraphQLStreamfield(field_name: str, **kwargs):
    def Mixin():
        from .types.streamfield import StreamFieldInterface

        return GraphQLField(field_name, graphene.List(StreamFieldInterface), **kwargs)

    return Mixin


def GraphQLImage(field_name: str, **kwargs):
    def Mixin():
        from .types.images import get_image_type, ImageObjectType

        return GraphQLField(field_name, get_image_type, **kwargs)

    return Mixin


def GraphQLDocument(field_name: str, **kwargs):
    from django.conf import settings

    document_type = "wagtaildocs.Document"
    if hasattr(settings, "WAGTAILDOCS_DOCUMENT_MODEL"):
        document_type = settings["WAGTAILDOCS_DOCUMENT_MODEL"]

    return GraphQLForeignKey(field_name, document_type, **kwargs)


def GraphQLMedia(field_name: str, **kwargs):
    def Mixin():
        from .types.media import MediaObjectType

        return GraphQLField(field_name, MediaObjectType, **kwargs)

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
    required=False,
    item_required=False,
    **kwargs
):
    def Mixin():
        from .types.structures import QuerySetList

        # Check if using nested field extracion:
        source = kwargs.get("source", None)
        if source and "." in source:
            source, *key = source.split(".")
            if key:
                kwargs["source"] = source
                kwargs["key"] = key

        # Create the nested type and wrap it in some list field.
        graphql_type = nested_type(field_name, *args, required=item_required, **kwargs)
        collection_type = graphene.List

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
            required_collection_type = lambda nested_type: graphene.NonNull(
                collection_type(nested_type)
            )

        return graphql_type, required_collection_type or collection_type

    return Mixin


def GraphQLEmbed(field_name: str):
    def Mixin():
        from .types.streamfield import EmbedBlock

        return GraphQLField(field_name, EmbedBlock)

    return Mixin
