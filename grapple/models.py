import graphene
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .registry import registry


# Classes used to define what the Django field should look like in the GQL type
class GraphQLField:
    field_name: str
    field_type: str
    field_source: str

    def __init__(self, field_name: str, field_type: type = None, **kwargs):
        self.field_name = field_name
        if callable(field_type):
            self.field_type = field_type()
        else:
            self.field_type = field_type
        if field_type:
            self.field_type.source = field_name
        self.field_source = kwargs.get("source", field_name)


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
        elif field_type:
            field_type = graphene.Field(field_type)

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

        return GraphQLField(field_name, graphene.Field(lambda: get_image_type()), **kwargs)

    return Mixin


def GraphQLDocument(field_name: str, **kwargs):
    from django.conf import settings

    document_type = "wagtaildocs.Document"
    if hasattr(settings, "WAGTAILDOCS_DOCUMENT_MODEL"):
        document_type = settings["WAGTAILDOCS_DOCUMENT_MODEL"]

    return GraphQLForeignKey(field_name, document_type, **kwargs)


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

        if field_type and is_list:
            field_type = graphene.List(field_type)
        elif field_type:
            field_type = graphene.Field(field_type)

        return GraphQLField(field_name, field_type, **kwargs)
        
    return Mixin


def GraphQLMedia(field_name: str, **kwargs):
    def Mixin():
        from .types.media import MediaObjectType

        return GraphQLField(field_name, MediaObjectType, **kwargs)

    return Mixin


def GraphQLPage(field_name: str):
    def Mixin():
        from .types.pages import PageInterface

        return GraphQLField(field_name, PageInterface)
    
    return Mixin


def GraphQLCollection(field_name: str, grapple_type, **kwargs):
    def Mixin():
        return GraphQLField(field_name, graphene.List(grapple_type), **kwargs)

    return Mixin
