import graphene

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
from wagtail.models import Page as WagtailPage
from wagtail.models import Site

from ..registry import registry
from ..utils import resolve_queryset, resolve_site_by_hostname
from .interfaces import get_page_interface
from .structures import QuerySetList


class Page(DjangoObjectType):
    """
    Base Page type used if one isn't generated for the current model.
    All other node types extend this.
    """

    class Meta:
        model = WagtailPage
        interfaces = (get_page_interface(),)


def get_preview_page(token):
    """
    Get a preview page from a token.
    """
    try:
        token_params_list = token.split(":").pop(0)
        token_params_kvstr = token_params_list.split(";")

        params = {}
        for arg in token_params_kvstr:
            key, value = arg.split("=")
            params[key] = value

        if _id := params.get("id"):
            """
            This is a page that had already been saved. Lookup the class and call get_page_from_preview_token.

            TODO: update headless preview to always send page_type in the token so we can always
            the if content_type branch and eliminate the if id branch.
            """
            if page := WagtailPage.objects.get(pk=_id).specific:
                cls = type(page)
                """
                get_page_from_preview_token is added by wagtail-headless-preview,
                this condition checks that headless-preview is installed and enabled
                for the model.
                """
                if hasattr(cls, "get_page_from_preview_token"):
                    """we assume that get_page_from_preview_token validates the token"""
                    return cls.get_page_from_preview_token(token)

        if content_type := params.get("page_type"):
            """
            this is a page which has not been saved yet. lookup the content_type to get the class
            and call get_page_from_preview_token.
            """
            app_label, model = content_type.lower().split(".")
            if ctype := ContentType.objects.get(app_label=app_label, model=model):
                cls = ctype.model_class()
                """
                get_page_from_preview_token is added by wagtail-headless-preview,
                this condition checks that headless-preview is installed and enabled
                for the model.
                """
                if hasattr(cls, "get_page_from_preview_token"):
                    """we assume that get_page_from_preview_token validates the token"""
                    return cls.get_page_from_preview_token(token)
    except (WagtailPage.DoesNotExist, ContentType.DoesNotExist, ValueError):
        """
        catch and suppress errors. we don't want to expose any information about unpublished content
        accidentally.
        TODO: consider logging here.
        """
        return None


def get_specific_page(
    id=None, slug=None, url_path=None, token=None, content_type=None, site=None
):
    """
    Get a specific page, given a page_id, slug or preview if a preview token is passed
    """
    page = None
    try:
        if token:
            return get_preview_page(token)

        # Everything but the special RootPage
        qs = WagtailPage.objects.live().public().filter(depth__gt=1).specific()

        if site:
            qs = qs.in_site(site)

        if content_type:
            app_label, model = content_type.lower().split(".")
            qs = qs.filter(
                content_type=ContentType.objects.get(app_label=app_label, model=model)
            )

        if id:
            page = qs.get(pk=id)
        elif slug:
            page = qs.get(slug=slug)
        elif url_path:
            if not url_path.endswith("/"):
                url_path += "/"

            if site:
                # Got a site, so make the url_path query as specific as possible
                qs = qs.filter(
                    url_path=f"{site.root_page.url_path}{url_path.lstrip('/')}"
                )
            else:
                # if the url_path is not specific enough, or the same url_path exists under multiple
                # site roots, only the first one will be returned.
                # To-Do: make site a 1st class argument on the page query, rather than just `in_site`
                qs = qs.filter(url_path__endswith=url_path)

            if qs.exists():
                page = qs.first()

    except WagtailPage.DoesNotExist:
        page = None

    return page


def get_site_filter(info, **kwargs):
    site_hostname = kwargs.pop("site", None)
    in_current_site = kwargs.get("in_site", False)

    if site_hostname is not None and in_current_site:
        raise GraphQLError(
            "The 'site' and 'in_site' filters cannot be used at the same time."
        )

    if site_hostname is not None:
        return resolve_site_by_hostname(
            hostname=site_hostname,
            filter_name="site",
        )
    elif in_current_site:
        return Site.find_for_request(info.context)


def PagesQuery():
    # Add base type to registry
    registry.pages[type(WagtailPage)] = Page

    class Mixin:
        pages = QuerySetList(
            graphene.NonNull(get_page_interface),
            content_type=graphene.Argument(
                graphene.String,
                description=_(
                    "Filter by content type. Uses the `app.Model` notation. Accepts a comma separated list of content types."
                ),
            ),
            in_site=graphene.Argument(
                graphene.Boolean,
                description=_("Filter to pages in the current site only."),
                default_value=False,
            ),
            site=graphene.Argument(
                graphene.String,
                description=_("Filter to pages in the give site."),
            ),
            ancestor=graphene.Argument(
                graphene.ID,
                description=_(
                    "Filter to pages that are descendants of the given page."
                ),
                required=False,
            ),
            parent=graphene.Argument(
                graphene.ID,
                description=_(
                    "Filter to pages that are children of the given page. "
                    "When using both `parent` and `ancestor`, then `parent` will take precendence."
                ),
                required=False,
            ),
            enable_search=True,
            enable_in_menu=True,
            required=True,
        )
        page = graphene.Field(
            get_page_interface(),
            id=graphene.ID(),
            slug=graphene.String(),
            url_path=graphene.Argument(
                graphene.String,
                description=_(
                    "Filter by url path. Note: in a multi-site setup, returns the first available page based. "
                    "Use `inSite: true` from the relevant site domain."
                ),
            ),
            token=graphene.Argument(
                graphene.String,
                description=_(
                    "Filter by preview token as passed by the `wagtail-headless-preview` package."
                ),
            ),
            content_type=graphene.Argument(
                graphene.String,
                description=_(
                    "Filter by content type using the app.ModelName notation. e.g. `myapp.BlogPage`"
                ),
            ),
            in_site=graphene.Argument(
                graphene.Boolean,
                description=_("Filter to pages in the current site only."),
                default_value=False,
            ),
            site=graphene.Argument(
                graphene.String,
                description=_("Filter to pages in the give site."),
            ),
        )

        # Return all pages in site, ideally specific.
        def resolve_pages(self, info, **kwargs):
            qs = WagtailPage.objects.all()

            try:
                if kwargs.get("parent"):
                    qs = WagtailPage.objects.get(id=kwargs.get("parent")).get_children()
                elif kwargs.get("ancestor"):
                    qs = WagtailPage.objects.get(
                        id=kwargs.get("ancestor")
                    ).get_descendants()
            except WagtailPage.DoesNotExist:
                qs = WagtailPage.objects.none()

            # no need to the root page
            pages = qs.live().public().filter(depth__gt=1).specific()

            site = get_site_filter(info, **kwargs)
            site_hostname = kwargs.get("site")
            in_current_site = kwargs.get("in_site", False)

            if site is not None:
                pages = pages.in_site(site)
            elif site is None and any(
                [site_hostname is not None, in_current_site is True]
            ):
                # If we could not resolve a Site but _were_ passed a filter, we
                # should not return any results.
                return WagtailPage.objects.none()

            content_type = kwargs.pop("content_type", None)
            content_types = content_type.split(",") if content_type else None
            if content_types:
                filters = Q()
                for content_type in content_types:
                    app_label, model = content_type.strip().lower().split(".")
                    filters |= Q(
                        content_type__app_label=app_label, content_type__model=model
                    )
                pages = pages.filter(filters)

            return resolve_queryset(pages, info, **kwargs)

        # Return a specific page, identified by ID or Slug.
        def resolve_page(self, info, **kwargs):
            return get_specific_page(
                id=kwargs.get("id"),
                slug=kwargs.get("slug"),
                url_path=kwargs.get("url_path"),
                token=kwargs.get("token"),
                content_type=kwargs.get("content_type"),
                site=get_site_filter(info, **kwargs),
            )

    return Mixin
