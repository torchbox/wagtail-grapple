import graphene

from django.conf import settings
from wagtail.contrib.redirects.models import Redirect

from ..registry import registry
from .pages import PageInterface


class RedirectType(graphene.ObjectType):
    old_path = graphene.String()
    old_url = graphene.String()
    new_url = graphene.String()
    page = graphene.Field(PageInterface)
    is_permanent = graphene.Boolean()

    # Give old_path with BASE_URL attached.
    def resolve_old_url(self, info, **kwargs):
        return settings.BASE_URL + self.old_path

    # Get new url
    def resolve_new_url(self, info, **kwargs):
        if self.redirect_page is None:
            return self.link

        return self.redirect_page.url_path

    # Return the page that's being redirected to, if at all.
    def resolve_page(self, info, **kwargs):
        if self.redirect_page is not None:
            return self.redirect_page.specific


class RedirectsQuery:
    redirects = graphene.List(RedirectType)

    # Return all redirects.
    def resolve_redirects(self, info, **kwargs):
        redirects = Redirect.objects.select_related("redirect_page")

        return Redirect.objects.select_related("redirect_page")
