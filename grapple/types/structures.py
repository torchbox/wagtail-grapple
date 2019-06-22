import inspect
import graphene
import graphene_django

from django.utils.translation import ugettext_lazy as _
from wagtail.search.index import class_is_indexed
from taggit.managers import _TaggableManager
from graphene.types import Int


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
                graphene.String, description=_("Use Django ordering format.")
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
