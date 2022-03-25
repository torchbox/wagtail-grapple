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
    def parse_literal(node):
        return_value = Int.parse_literal(node)
        if return_value is not None:
            if return_value >= 0:
                return return_value


class QuerySetList(graphene.List):
    """
    List type with arguments used by Django's query sets.

    This list setts the following arguments on itself:

    * ``id``
    * ``limit``
    * ``offset``
    * ``search_query``
    * ``order``

    :param enable_limit: Enable limit argument.
    :type enable_limit: bool
    :param enable_offset: Enable offset argument.
    :type enable_offset: bool
    :param enable_search: Enable search query argument.
    :type enable_search: bool
    :param enable_order: Enable ordering via query argument.
    :type enable_order: bool
    """

    def __init__(self, of_type, *args, **kwargs):
        enable_limit = kwargs.pop("enable_limit", True)
        enable_offset = kwargs.pop("enable_offset", True)
        enable_search = kwargs.pop("enable_search", True)
        enable_order = kwargs.pop("enable_order", True)

        # Check if the type is a Django model type. Do not perform the
        # check if value is lazy.
        if inspect.isclass(of_type) and not issubclass(
            of_type, graphene_django.DjangoObjectType
        ):
            raise TypeError(
                f"{of_type} is not a subclass of DjangoObjectType and it "
                "cannot be used with QuerySetList."
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
                    "Number of records skipped from the beginning of the "
                    "results set."
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

    This type setts the following arguments on itself:

    * ``id``
    * ``page``
    * ``per_page``
    * ``search_query``
    * ``order``

    :param enable_search: Enable search query argument.
    :type enable_search: bool
    :param enable_order: Enable ordering via query argument.
    :type enable_order: bool
    """

    enable_search = kwargs.pop("enable_search", True)
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

    if "id" not in kwargs:
        kwargs["id"] = graphene.Argument(graphene.ID, description=_("Filter by ID"))

    class PaginatedType(BasePaginatedType):
        items = graphene.List(of_type, required=required)
        pagination = graphene.Field(PaginationType, required=required)

        class Meta:
            name = type_name + "PaginatedType"

    return graphene.Field(PaginatedType, **kwargs)
