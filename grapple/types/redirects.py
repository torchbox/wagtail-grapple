from typing import Optional

import graphene

from django.conf import settings
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page

from .pages import get_page_interface


class RedirectType(graphene.ObjectType):
    old_path = graphene.String(required=True)
    old_url = graphene.String(required=True)
    new_url = graphene.String(required=False)
    page = graphene.Field(get_page_interface())
    is_permanent = graphene.Boolean(required=True)

    # Give old_path with BASE_URL attached.
    def resolve_old_url(self, info, **kwargs) -> str:
        return settings.BASE_URL + self.old_path

    # Get new url
    def resolve_new_url(self, info, **kwargs) -> Optional[str]:
        if self.redirect_page:
            return self.redirect_page.url

        if self.link:
            return self.link

        return None

    # Return the page that's being redirected to, if at all.
    def resolve_page(self, info, **kwargs) -> Optional[Page]:
        if self.redirect_page is not None:
            return self.redirect_page.specific


class RedirectsQuery:
    redirects = graphene.List(graphene.NonNull(RedirectType), required=True)

    # Return all redirects.
    def resolve_redirects(self, info, **kwargs):
        return Redirect.objects.select_related("redirect_page")
