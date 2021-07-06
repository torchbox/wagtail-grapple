from django.db import models

from wagtail.documents.models import Document, AbstractDocument

from grapple.models import GraphQLString


class CustomDocument(AbstractDocument):
    admin_form_fields = Document.admin_form_fields

    def custom_document_property(self, info, **kwargs):
        return "Document Model!"

    graphql_fields = (GraphQLString("custom_document_property", required=True),)
