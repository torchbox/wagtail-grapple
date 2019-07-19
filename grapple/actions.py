import graphene
import inspect
from typing import Type
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from wagtail.contrib.settings.models import BaseSetting
from wagtail.core.models import Page as WagtailPage
from wagtail.documents.models import AbstractDocument
from wagtail.images.models import AbstractImage
from wagtail.snippets.models import get_snippet_models
from graphene_django.types import DjangoObjectType


from .registry import registry
from .types.pages import PageInterface, Page
from .types.documents import DocumentObjectType
from .types.images import ImageObjectType


def import_apps():
    """
    Add each django app set in the settings file
    """
    apps = settings.GRAPPLE_APPS.items()
    for name, prefix in apps:
        add_app(name, prefix)
        registry.apps.append(name)


def add_app(app: str, prefix: str = ""):
    """
    Iterate through each model in the app and pass it to node type creators.
    """

    # Create a collection of models of standard models (Pages, Images,
    # Documents).
    models = [
        mdl.model_class() for mdl in ContentType.objects.filter(app_label=app).all()
    ]

    # Add snippet models to model collection.
    for snippet in get_snippet_models():
        if snippet._meta.app_label == app:
            models.append(snippet)

    # Create add each model to correct section of registry.
    for model in models:
        register_model(model, prefix)


def register_model(cls: type, type_prefix: str):
    """
    Pass model to the right node type creator based on it's base class.
    """

    # Pass class to correct type creator.
    if cls is not None:
        if issubclass(cls, WagtailPage):
            register_page_model(cls, type_prefix)
        elif issubclass(cls, AbstractDocument):
            register_documment_model(cls, type_prefix)
        elif issubclass(cls, AbstractImage):
            register_image_model(cls, type_prefix)
        elif issubclass(cls, BaseSetting):
            register_settings_model(cls, type_prefix)
        elif cls in get_snippet_models():
            register_snippet_model(cls, type_prefix)
        else:
            register_django_model(cls, type_prefix)


def get_fields_and_properties(cls):
    """
    Return all fields and @property methods for a model.
    """
    fields = [field.name for field in cls._meta.get_fields(include_parents=False)]
    properties = []
    try:
        properties = [
            method[0]
            for method in inspect.getmembers(cls, lambda o: isinstance(o, property))
        ]
    except BaseException:
        properties = []

    return fields + properties


def build_node_type(
    cls: type,
    type_prefix: str,
    interface: graphene.Interface,
    base_type: Type[DjangoObjectType] = DjangoObjectType,
):
    """
    Build a graphene node type from a model class and associate
    with an interface. If it has custom fields then implmement them.
    """
    type_name = type_prefix + cls.__name__

    # Create a new blank node type
    class Meta:
        model = cls
        interfaces = (interface,) if interface is not None else tuple()
        exclude_fields = tuple()

    type_meta = {"Meta": Meta}
    type_meta.update({"id": graphene.ID()})

    # Build a list fields that shouldn't be reflected in GQL type.
    exclude_fields = get_fields_and_properties(cls)

    # Add any custom fields to node if they are defined.
    if hasattr(cls, "graphql_fields"):
        for field in cls.graphql_fields:
            if callable(field):
                field = field()

            # Take current field out of exclude_fields array
            if field.field_name in exclude_fields:
                exclude_fields.remove(field.field_name)

            # Add field to GQL type with correct field-type
            if field.field_type is not None:
                type_meta[field.field_name] = field.field_type

    # Set excluded fields to stop errors cropping up from unsupported field
    # types.
    type_meta["Meta"].exclude_fields = exclude_fields

    return type(type_name, (base_type,), type_meta)


def register_page_model(cls: Type[WagtailPage], type_prefix: str):
    """
    Create graphene node type for models than inherit from Wagtail Page model.
    """

    # Avoid gql type duplicates
    if cls in registry.pages:
        return

    # Create a GQL type derived from page model.
    page_node_type = build_node_type(cls, type_prefix, PageInterface, Page)

    # Add page type to registry.
    if page_node_type:
        registry.pages[cls] = page_node_type


def register_documment_model(cls: Type[AbstractDocument], type_prefix: str):
    """
    Create graphene node type for a model than inherits from AbstractDocument.
    Only one model will actually be generated because a default document model
    needs to be set in settings.
    """

    # Avoid gql type duplicates
    if cls in registry.documents:
        return

    # Create a GQL type derived from document model.
    document_node_type = build_node_type(cls, type_prefix, None, DocumentObjectType)

    # Add document type to registry.
    if document_node_type:
        registry.documents[cls] = document_node_type


def register_image_model(cls: Type[AbstractImage], type_prefix: str):
    """
    Create a graphene node type for a model than inherits from AbstractImage.
    Only one model will actually be generated because a default image model
    needs to be set in settings.
    """

    # Avoid gql type duplicates
    if cls in registry.images:
        return

    # Create a GQL type derived from document model.
    image_node_type = build_node_type(cls, type_prefix, None, ImageObjectType)

    # Add image type to registry.
    if image_node_type:
        registry.images[cls] = image_node_type


def register_settings_model(cls: Type[BaseSetting], type_prefix: str):
    """
    Create a graphene node type for a settings page.
    """

    # Avoid gql type duplicates
    if cls in registry.settings:
        return

    # Create a GQL type derived from document model.
    settings_node_type = build_node_type(cls, type_prefix, None)

    # Add image type to registry.
    if settings_node_type:
        registry.settings[cls] = settings_node_type


def register_snippet_model(cls: Type[models.Model], type_prefix: str):
    """
    Create a graphene type for a snippet model.
    """

    # Avoid gql type duplicates
    if cls in registry.snippets:
        return

    # Create a GQL type that implements Snippet Interface
    snippet_node_type = build_node_type(cls, type_prefix, None)

    if snippet_node_type:
        registry.snippets[cls] = snippet_node_type


def register_django_model(cls: Type[models.Model], type_prefix: str):
    """
    Create a graphene type for (non-specific) django model.
    Used for Orderables and other foreign keys.
    """

    # Avoid gql type duplicates
    if cls in registry.django_models:
        return

    # Create a GQL type that implements Snippet Interface
    django_node_type = build_node_type(cls, type_prefix, None)

    if django_node_type:
        registry.django_models[cls] = django_node_type
