import inspect

import graphene
import graphene_django

from django.utils.translation import gettext_lazy as _
from graphene.types import Int
from taggit.managers import _TaggableManager
from wagtail.search.index import class_is_indexed


class PositiveInt(Int):
    """
    GraphQL type for an integer that must be equal or greater than zero.
    """

    @staticmethod
    def parse_literal(ast, _variables=None):
        return_value = Int.parse_literal(ast, _variables=_variables)
        if return_value is not None and return_value >= 0:
            return return_value


class SearchOperatorEnum(graphene.Enum):
    """
    Enum for search operator.
    """

    AND = "and"
    OR = "or"

    def __str__(self):
        # the core search parser expects the operator to be a string.
        # the default __str__ returns SearchOperatorEnum.AND/OR,
        # this __str__ returns the value and/or for compatibility.
        return self.value


class QuerySetList(graphene.List):
    """
    List type with arguments used by Django's query sets.

    This list setts the following arguments on itself:

    * ``id``
    * ``in_menu``
    * ``limit``
    * ``offset``
    * ``search_query``
    * ``search_operator``
    * ``order``

    :param enable_in_menu: Enable in_menu filter.
    :type enable_in_menu: bool
    :param enable_limit: Enable limit argument.
    :type enable_limit: bool
    :param enable_offset: Enable offset argument.
    :type enable_offset: bool
    :param enable_search: Enable search query argument.
    :type enable_search: bool
    :param enable_search_operator: Enable search operator argument, enable_search must also be True
    :type enable_search_operator: bool
    :param enable_order: Enable ordering via query argument.
    :type enable_order: bool
    """

    def __init__(self, of_type, *args, **kwargs):
        enable_in_menu = kwargs.pop("enable_in_menu", False)
        enable_limit = kwargs.pop("enable_limit", True)
        enable_offset = kwargs.pop("enable_offset", True)
        enable_order = kwargs.pop("enable_order", True)
        enable_search = kwargs.pop("enable_search", True)
        enable_search_operator = kwargs.pop("enable_search_operator", True)

        # Check if the type is a Django model type. Do not perform the
        # check if value is lazy.
        if inspect.isclass(of_type) and not issubclass(
            of_type, graphene_django.DjangoObjectType
        ):
            raise TypeError(
                f"{of_type} is not a subclass of DjangoObjectType and it "
                "cannot be used with QuerySetList."
            )

        # Enable in_menu for Page models.
        if enable_in_menu is True and "in_menu" not in kwargs:
            kwargs["in_menu"] = graphene.Argument(
                graphene.Boolean,
                description=_(
                    "Filter pages by Page.show_in_menus property. That is, the "
                    "'show in menus' checkbox is checked in the page editor."
                ),
            )
        # Enable limiting on the queryset.
        if enable_limit is True and "limit" not in kwargs:
            kwargs["limit"] = graphene.Argument(
                PositiveInt, description=_("Limit a number of resulting objects.")
            )

        # Enable offset on the queryset.
        if enable_offset is True and "offset" not in kwargs:
            kwargs["offset"] = graphene.Argument(
                PositiveInt,
                description=_(
                    "Number of records skipped from the beginning of the results set."
                ),
            )

        # Enable ordering of the queryset
        if enable_order is True and "order" not in kwargs:
            kwargs["order"] = graphene.Argument(
                graphene.String, description=_("Use the Django queryset order format.")
            )

        # If type is provided as a lazy value (e.g. using lambda), then
        # the search has to be enabled explicitly.
        if (enable_search is True and not inspect.isclass(of_type)) or (
            enable_search is True
            and inspect.isclass(of_type)
            and class_is_indexed(of_type._meta.model)
            and "search_query" not in kwargs
        ):
            kwargs["search_query"] = graphene.Argument(
                graphene.String,
                description=_("Filter the results using Wagtail's search."),
            )
            if enable_search_operator:
                kwargs["search_operator"] = graphene.Argument(
                    SearchOperatorEnum,
                    description=_(
                        "Specify search operator (and/or), see: https://docs.wagtail.org/en/stable/topics/search/searching.html#search-operator"
                    ),
                    default_value="and",
                )

        if "id" not in kwargs:
            kwargs["id"] = graphene.Argument(graphene.ID, description=_("Filter by ID"))

        super().__init__(of_type, *args, **kwargs)


class TagList(graphene.JSONString):
    """
    A tag list from the TaggableManager.
    """

    @staticmethod
    def serialize(value):
        if isinstance(value, _TaggableManager):
            return list(value.values_list("name", flat=True))
        raise ValueError("Cannot convert tags object")


class PaginationType(graphene.ObjectType):
    """
    GraphQL type for Paginated QuerySet pagination field.
    """

    total = PositiveInt(required=True)
    count = PositiveInt(required=True)
    per_page = PositiveInt(required=True)
    current_page = PositiveInt(required=True)
    prev_page = PositiveInt()
    next_page = PositiveInt()
    total_pages = PositiveInt(required=True)


class BasePaginatedType(graphene.ObjectType):
    """
    GraphQL type for Paginated QuerySet result.
    """

    items = graphene.List(graphene.String)
    pagination = graphene.Field(PaginationType)


def PaginatedQuerySet(of_type, type_class, **kwargs):
    """
    Paginated QuerySet type with arguments used by Django's query sets.

    This type sets the following arguments on itself:

    * ``id``
    * ``in_menu``
    * ``page``
    * ``per_page``
    * ``search_query``
    * ``search_operator``
    * ``order``

    :param enable_search: Enable search query argument.
    :type enable_search: bool
    :param enable_search_operator: Enable search operator argument, enable_search must also be True
    :type enable_search_operator: bool
    :param enable_order: Enable ordering via query argument.
    :type enable_order: bool
    """

    enable_in_menu = kwargs.pop("enable_in_menu", False)
    enable_search = kwargs.pop("enable_search", True)
    enable_search_operator = kwargs.pop("enable_search_operator", True)
    enable_order = kwargs.pop("enable_order", True)
    required = kwargs.get("required", False)
    type_name = type_class if isinstance(type_class, str) else type_class.__name__
    type_name = type_name.lstrip("Stub")

    # Check if the type is a Django model type. Do not perform the
    # check if value is lazy.
    if inspect.isclass(of_type) and not issubclass(
        of_type, graphene_django.DjangoObjectType
    ):
        raise TypeError(
            f"{of_type} is not a subclass of DjangoObjectType and it "
            "cannot be used with QuerySetList."
        )

    # Enable in_menu for Page models.
    if enable_in_menu is True and "in_menu" not in kwargs:
        kwargs["in_menu"] = graphene.Argument(
            graphene.Boolean,
            description=_(
                "Filter pages by Page.show_in_menus property. That is, the "
                "'show in menus' checkbox is checked in the page editor."
            ),
        )

    # Enable page for Django Paginator.
    if "page" not in kwargs:
        kwargs["page"] = graphene.Argument(
            PositiveInt,
            description=_("Page of resulting objects to return."),
        )

    # Enable per_page for Django Paginator.
    if "per_page" not in kwargs:
        kwargs["per_page"] = graphene.Argument(
            PositiveInt,
            description=_("The maximum number of items to include on a page."),
        )

    # Enable ordering of the queryset
    if enable_order is True and "order" not in kwargs:
        kwargs["order"] = graphene.Argument(
            graphene.String, description=_("Use the Django QuerySet order_by format.")
        )

    # If type is provided as a lazy value (e.g. using lambda), then
    # the search has to be enabled explicitly.
    if (enable_search is True and not inspect.isclass(of_type)) or (
        enable_search is True
        and inspect.isclass(of_type)
        and class_is_indexed(of_type._meta.model)
        and "search_query" not in kwargs
    ):
        kwargs["search_query"] = graphene.Argument(
            graphene.String, description=_("Filter the results using Wagtail's search.")
        )
        if enable_search_operator:
            kwargs["search_operator"] = graphene.Argument(
                SearchOperatorEnum,
                description=_(
                    "Specify search operator (and/or), see: https://docs.wagtail.org/en/stable/topics/search/searching.html#search-operator"
                ),
                default_value="and",
            )

    if "id" not in kwargs:
        kwargs["id"] = graphene.Argument(graphene.ID, description=_("Filter by ID"))

    class PaginatedType(BasePaginatedType):
        items = graphene.List(of_type, required=required)
        pagination = graphene.Field(PaginationType, required=required)

        class Meta:
            name = type_name + "PaginatedType"

    return graphene.Field(PaginatedType, **kwargs)
