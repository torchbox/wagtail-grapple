import copy

from typing import List, Optional
from urllib.parse import urlparse

import graphene

from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site

from grapple.types.sites import SiteObjectType

from .pages import get_page_interface


class RedirectObjectType(graphene.ObjectType):
    old_path = graphene.String(required=True)
    old_url = graphene.String(required=True)
    new_url = graphene.String(required=False)
    page = graphene.Field(get_page_interface())
    site = graphene.Field(
        SiteObjectType, required=True
    )  # Required because `RedirectsQuery` always adds a value.
    is_permanent = graphene.Boolean(required=True)

    class Meta:
        name = "Redirect"

    def resolve_old_url(self: Redirect, info, **kwargs) -> str:
        """
        Resolve the value of `old_url` using the `root_url` of the associated
        site and `old_path`.
        """

        return self.site.root_url + self.old_path

    def resolve_new_url(self: Redirect, info, **kwargs) -> Optional[str]:
        """
        Resolve the value of `new_url`. If `redirect_page` is specified then
        `link` is used. Otherwise, ensure that the redirect link is absolute.
        """
        if self.redirect_page:
            return self.link  # Handled by the `Redirect` model

        elif self.redirect_link:
            parsed_url = urlparse(self.redirect_link)

            if not parsed_url.scheme:  # url without scheme is not absolute
                return (
                    self.site.root_url.rstrip("/")
                    + "/"
                    + self.redirect_link.lstrip("/")
                )
            else:
                return self.redirect_link

        else:
            return None

    # Return the page that's being redirected to, if at all.
    def resolve_page(self: Redirect, info, **kwargs) -> Optional[Page]:
        if self.redirect_page is not None:
            return self.redirect_page.specific


class RedirectsQuery:
    redirects = graphene.List(graphene.NonNull(RedirectObjectType), required=True)

    # Return all redirects.
    def resolve_redirects(self, info, **kwargs) -> List[Redirect]:
        """
        Resolve the query set of redirects. If `site` is None, a redirect works
        for all sites. To show this, a new redirect object is created for each
        of the sites.
        """

        redirects_qs = (
            Redirect.objects.select_related("redirect_page")
            .select_related("site")
            .all()
        )
        finalised_redirects: list[Redirect] = []  # Redirects to return in API.

        for redirect in redirects_qs:
            if redirect.site is None:
                # Duplicate Redirect for each Site as it applies to all Sites.
                for site in Site.objects.all():
                    _new_redirect = copy.deepcopy(redirect)
                    _new_redirect.site = site
                    finalised_redirects.append(_new_redirect)
            else:
                finalised_redirects.append(redirect)
        return finalised_redirects
