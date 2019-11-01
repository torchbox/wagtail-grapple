import graphene
from graphene_django import DjangoObjectType
from wagtailmedia.models import Media
from django.conf import settings


class MediaObjectType(DjangoObjectType):
    class Meta:
        model = Media
        exclude_fields = ("tags",)

    def resolve_file(self, info, **kwargs):
        if self.file.url[0] == "/":
            return settings.BASE_URL + self.file.url
        return self.file.url
