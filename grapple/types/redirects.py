import json

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
        If the redirect is for a specific site, append hostname and port to path.
        Otherwise, return a JSON string representing a list of all site urls.
        """
        if self.site:
            return f"{self.site.root_url}/{self.old_path}"

        # TODO: Remove after making site required
        if self.site is None:
            sites_QS = Site.objects.all()
            old_url_list = []
            for site in sites_QS:
                url = f"http://{site.hostname}:{site.port}/{self.old_path}"
                old_url_list.append(url)

            json_string = json.dumps(old_url_list)
            return json_string

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
        return Redirect.objects.select_related("redirect_page")
