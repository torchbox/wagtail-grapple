import copy

from typing import Optional

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
    site = graphene.Field(SiteObjectType, required=False)
    is_permanent = graphene.Boolean(required=True)

    def resolve_old_url(self, info, **kwargs) -> str:
        """
        Resolve the value of `old_url` using the `root_url` of the associated
        site and `old_path`.
        Note: `self.site` should never be none because of `resolve_redirects`.
        """
        if self.site:
            return f"{self.site.root_url}/{self.old_path}"

        if self.site is None:
            return None

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

    class Meta:
        name = "Redirect"


class RedirectsQuery:
    redirects = graphene.List(graphene.NonNull(RedirectObjectType), required=True)

    # Return all redirects.
    def resolve_redirects(self, info, **kwargs):
        """
        Resolve the query set of redirects. If `site` is None, a redirect works
        for all sites. To show this, a new redirect object is created for each
        of the sites.
        """
        redirects_QS = Redirect.objects.select_related("redirect_page")
        redirect_list = list(redirects_QS)
        sites_QS = Site.objects.all()
        for redirect in redirect_list:
            if redirect.site is None:
                for site in sites_QS:
                    new_redirect = copy.copy(redirect)
                    new_redirect.site = site
                    redirect_list.append(new_redirect)

        redirect_list = filter(lambda x: (x.site is not None), redirect_list)

        return redirect_list
