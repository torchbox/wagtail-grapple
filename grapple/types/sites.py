import graphene
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from graphene_django.types import DjangoObjectType
from graphql.error import GraphQLError

try:
    from wagtail.models import Page as WagtailPage
    from wagtail.models import Site
except ImportError:
    from wagtail.core.models import Page as WagtailPage
    from wagtail.core.models import Site

from ..utils import resolve_queryset, resolve_site
from .pages import PageInterface, get_specific_page
from .structures import QuerySetList


class SiteObjectType(DjangoObjectType):
    pages = QuerySetList(
        graphene.NonNull(lambda: PageInterface),
        content_type=graphene.Argument(
            graphene.String,
            description=_("Filter by content type. Uses the `app.Model` notation."),
        ),
        enable_search=True,
        required=True,
    )
    page = graphene.Field(
        PageInterface,
        id=graphene.Int(),
        slug=graphene.String(),
        url_path=graphene.String(),
        token=graphene.String(),
        content_type=graphene.String(),
    )

    def resolve_pages(self, info, **kwargs):
        pages = WagtailPage.objects.in_site(self).live().public().specific()

        content_type = kwargs.pop("content_type", None)
        if content_type:
            app_label, model = content_type.strip().lower().split(".")
            try:
                ctype = ContentType.objects.get(app_label=app_label, model=model)
            except ContentType.DoesNotExist:
                return (
                    WagtailPage.objects.none()
                )  # something not quite right here, bail out early
            else:
                pages = pages.filter(content_type=ctype)

        return resolve_queryset(pages, info, **kwargs)

    def resolve_page(self, info, **kwargs):
        return get_specific_page(
            id=kwargs.get("id"),
            slug=kwargs.get("slug"),
            url_path=kwargs.get("url_path"),
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

            if id:
                return Site.objects.filter(pk=id).first()
            elif hostname:
                try:
                    return resolve_site(hostname)
                except Site.MultipleObjectsReturned:
                    raise GraphQLError(
                        "Your 'hostname' filter value of '{}' returned multiple sites. Try adding a port number (for example: '{}:80').".format(
                            hostname, hostname
                        )
                    )

    return Mixin
