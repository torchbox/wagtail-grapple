import graphene
from graphene_django import DjangoObjectType
from ..registry import registry
from wagtailmedia.models import Media


class MediaObjectType(DjangoObjectType):
    value = graphene.String()
    
    class Meta:
        model = Media
