import graphene

from wagtail.core.models import Page as WagtailPage, Site
from graphene_django.types import DjangoObjectType

from ..utils import resolve_queryset
from .pages import PageInterface, get_specific_page
from .structures import QuerySetList


class SiteObjectType(DjangoObjectType):
    pages = QuerySetList(
        graphene.NonNull(lambda: PageInterface), enable_search=True, required=True
    )
    page = graphene.Field(
        PageInterface,
        id=graphene.Int(),
        slug=graphene.String(),
        token=graphene.String(),
        content_type=graphene.String(),
    )

    def resolve_pages(self, info, **kwargs):
        return resolve_queryset(
            WagtailPage.objects.in_site(self).live().public().specific(), info, **kwargs
        )

    def resolve_page(self, info, **kwargs):
        return get_specific_page(
            id=kwargs.get("id"),
            slug=kwargs.get("slug"),
            token=kwargs.get("token"),
            content_type=kwargs.get("content_type"),
            site=self,
        )

    class Meta:
        model = Site


def SitesQuery():
    class Mixin:
        site = graphene.Field(
            SiteObjectType, hostname=graphene.String(), id=graphene.ID()
        )
        sites = QuerySetList(
            graphene.NonNull(SiteObjectType), enable_search=True, required=True
        )

        # Return all sites.
        def resolve_sites(self, info, **kwargs):
            return resolve_queryset(Site.objects.all(), info, **kwargs)

        # Return a site, identified by ID or hostname.
        def resolve_site(self, info, **kwargs):
            id, hostname = kwargs.get("id"), kwargs.get("hostname")

            try:
                if id:
                    return Site.objects.get(pk=id)
                elif hostname:
                    return Site.objects.get(hostname=hostname)
            except BaseException:
                return None

    return Mixin
