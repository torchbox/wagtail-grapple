from django.db import models
from wagtail.documents.models import AbstractDocument, Document
from wagtail.images.models import AbstractImage, AbstractRendition, Image

from grapple.models import GraphQLString


class CustomDocument(AbstractDocument):
    admin_form_fields = Document.admin_form_fields

    def custom_document_property(self, info, **kwargs):
        return "Document Model!"

    graphql_fields = (GraphQLString("custom_document_property", required=True),)


class CustomImage(AbstractImage):
    admin_form_fields = Image.admin_form_fields

    def custom_image_property(self, info, **kwargs):
        return "Image Model!"

    graphql_fields = (GraphQLString("custom_image_property", required=True),)


class CustomImageRendition(AbstractRendition):
    image = models.ForeignKey(
        "CustomImage", related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)

    def custom_rendition_property(self, info, **kwargs):
        return "Rendition Model!"

    graphql_fields = (GraphQLString("custom_rendition_property", required=True),)
