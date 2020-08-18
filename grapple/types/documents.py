import graphene

from graphene_django.types import DjangoObjectType

from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.documents.models import Document as WagtailDocument

if WAGTAIL_VERSION < (2, 9):
    from wagtail.documents.models import get_document_model
else:
    from wagtail.documents import get_document_model

from ..registry import registry
from ..utils import get_media_item_url, resolve_queryset
from .structures import QuerySetList


class DocumentObjectType(DjangoObjectType):
    """
    Base document type used if one isn't generated for the current model.
    All other node types extend this.
    """

    class Meta:
        model = WagtailDocument
        exclude_fields = ("tags",)

    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    file = graphene.String(required=True)
    created_at = graphene.DateTime(required=True)
    file_size = graphene.Int()
    file_hash = graphene.String()
    url = graphene.String(required=True)

    def resolve_url(self, info):
        """
        Get document file url.
        """
        return get_media_item_url(self)


def DocumentsQuery():
    registry.documents[WagtailDocument] = DocumentObjectType
    mdl = get_document_model()
    model_type = registry.documents[mdl]

    class Mixin:
        documents = QuerySetList(
            graphene.NonNull(model_type), enable_search=True, required=True
        )

        # Return all pages, ideally specific.
        def resolve_documents(self, info, **kwargs):
            return resolve_queryset(mdl.objects.all(), info, **kwargs)

    return Mixin


def get_document_type():
    registry.documents[WagtailDocument] = DocumentObjectType
    mdl = get_document_model()
    return registry.documents[mdl]
