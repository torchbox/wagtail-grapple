import graphene
from graphene_django import DjangoObjectType
from wagtailmedia.models import Media
from django.conf import settings

class MediaObjectType(DjangoObjectType):
    class Meta:
        model = Media
        exclude_fields=('tags',)

    def resolve_file(self, info, **kwargs):
        return settings.BASE_URL + self.file.url
