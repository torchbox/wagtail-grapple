import graphene
from graphene_django.types import DjangoObjectType
from wagtail.documents import get_document_model
from wagtail.documents.models import Document as WagtailDocument

from ..registry import registry
from ..utils import get_media_item_url, resolve_queryset
from .collections import CollectionObjectType
from .structures import QuerySetList
from .tags import TagObjectType


class DocumentObjectType(DjangoObjectType):
    """
    Base document type used if one isn't generated for the current model.
    All other node types extend this.
    """

    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    file = graphene.String(required=True)
    created_at = graphene.DateTime(required=True)
    file_size = graphene.Int()
    file_hash = graphene.String(required=True)
    url = graphene.String(required=True)
    collection = graphene.Field(lambda: CollectionObjectType, required=True)
    tags = graphene.List(graphene.NonNull(lambda: TagObjectType), required=True)

    def resolve_url(self, info, **kwargs):
        """
        Get document file url.
        """
        return get_media_item_url(self)

    def resolve_tags(self, info, **kwargs):
        return self.tags.all()

    class Meta:
        model = WagtailDocument


def get_document_type():
    mdl = get_document_model()
    return registry.documents.get(mdl, DocumentObjectType)


def DocumentsQuery():
    mdl = get_document_model()
    mdl_type = get_document_type()

    class Mixin:
        document = graphene.Field(mdl_type, id=graphene.ID())
        documents = QuerySetList(
            graphene.NonNull(mdl_type),
            enable_search=True,
            required=True,
            collection=graphene.Argument(
                graphene.ID, description="Filter by collection id"
            ),
        )
        document_type = graphene.String(required=True)

        def resolve_document(self, info, id, **kwargs):
            """Returns a document given the id, if in a public collection"""
            try:
                return mdl.objects.filter(
                    collection__view_restrictions__isnull=True
                ).get(pk=id)
            except BaseException:
                return None

        def resolve_documents(self, info, **kwargs):
            """Returns all documents in a public collection"""
            qs = mdl.objects.filter(collection__view_restrictions__isnull=True)
            return resolve_queryset(qs, info, **kwargs)

        def resolve_document_type(self, info, **kwargs):
            return get_document_type()

    return Mixin
