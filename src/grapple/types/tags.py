import graphene
from graphene_django.converter import convert_django_field
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.managers import TaggableManager
from taggit.models import Tag

from grapple.utils import resolve_queryset

from .structures import QuerySetList


@convert_django_field.register(TaggableManager)
@convert_django_field.register(ClusterTaggableManager)
def convert_tag_manager_to_string(field, registry=None):
    return TagObjectType()


class TagObjectType(graphene.ObjectType):
    tag_id = graphene.ID(name="id", required=True)
    name = graphene.String(required=True)

    def resolve_tag_id(self, info, **kwargs):
        return self.id

    def resolve_name(self, info, **kwargs):
        return self.name


def TagsQuery():
    class Mixin:
        tag = graphene.Field(TagObjectType, id=graphene.ID())
        tags = QuerySetList(
            graphene.NonNull(TagObjectType), required=True, enable_search=False
        )

        def resolve_tag(self, info, id, **kwargs):
            try:
                return Tag.objects.get(pk=id)
            except BaseException:
                return None

        def resolve_tags(self, info, **kwargs):
            return resolve_queryset(Tag.objects.all(), info, **kwargs)

    return Mixin
