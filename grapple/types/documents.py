from wagtail.documents.models import Document as WagtailDocument, get_document_model
from graphene_django.types import DjangoObjectType
import graphene

from ..registry import registry
from ..utils import resolve_queryset
from .structures import QuerySetList


class DocumentObjectType(DjangoObjectType):
    """
    Base document type used if one isn't generated for the current model.
    All other node types extend this.
    """

    class Meta:
        model = WagtailDocument
        exclude_fields = ("tags",)

    id = graphene.ID()
    title = graphene.String()
    file = graphene.String()
    created_at = graphene.DateTime()
    file_size = graphene.Int()
    file_hash = graphene.String()


def DocumentsQuery():
    registry.documents[WagtailDocument] = DocumentObjectType
    mdl = get_document_model()
    model_type = registry.documents[mdl]

    class Mixin:
        documents = QuerySetList(model_type, enable_search=True)

        # Return all pages, ideally specific.
        def resolve_documents(self, info, **kwargs):
            return resolve_queryset(mdl.objects.all(), info, **kwargs)

    return Mixin


def get_document_type():
    registry.documents[WagtailDocument] = DocumentObjectType
    mdl = get_document_model()
    return registry.documents[mdl]
