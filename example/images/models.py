from django.db import models

from wagtail.images.models import Image, AbstractImage, AbstractRendition

from grapple.models import GraphQLString, GraphQLInt, GraphQLImage


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

    graphql_fields = (
        GraphQLString("custom_rendition_property", required=True),
        GraphQLInt("id", required=True),
        GraphQLString("url", required=True),
        GraphQLString("width", required=True),
        GraphQLString("height", required=True),
        GraphQLImage("image", required=True),
        GraphQLString("file", required=True),
    )
