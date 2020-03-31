import os
import base64
import tempfile
from PIL import Image, ImageFilter
from django.conf import settings
from wagtail.search.index import class_is_indexed
from wagtail.search.models import Query
from wagtail.search.backends import get_search_backend


def resolve_queryset(
    qs, info, limit=None, offset=None, search_query=None, id=None, order=None, **kwargs
):
    """
    Add limit, offset and search capabilities to the query. This contains
    argument names used by
    :class:`~wagtail_graphql.types.structures.QuerySetList`.
    :param qs: Query set to be modified.
    :param info: Graphene's info object.
    :param limit: Limit number of objects in the QuerySet.
    :type limit: int
    :param id: Filter by the primary key.
    :type limit: int
    :param offset: Omit a number of objects from the beggining of the query set
    :type offset: int
    :param search_query: Using wagtail search exclude objects that do not match
                         the search query.
    :type search_query: str
    :param order: Use Django ordering format to order the query set.
    :type order: str
    """
    offset = int(offset or 0)

    if id is not None:
        qs = qs.filter(pk=id)
    else:
        qs = qs.all()

    if id is None and search_query:
        # Check if the queryset is searchable using Wagtail search.
        if not class_is_indexed(qs.model):
            raise TypeError("This data type is not searchable by Wagtail.")

        if settings.GRAPPLE_ADD_SEARCH_HIT is True:
            query = Query.get(search_query)
            query.add_hit()

        return get_search_backend().search(search_query, qs)

    if order is not None:
        qs = qs.order_by(*map(lambda x: x.strip(), order.split(",")))

    if limit is not None:
        limit = int(limit)
        qs = qs[offset : limit + offset]

    return qs


def image_as_base64(image_file, format="png"):
    """
    :param `image_file` for the complete path of image.
    :param `format` is format for image, eg: `png` or `jpg`.
    """
    encoded_string = ""
    image_file = settings.BASE_DIR + image_file

    if not os.path.isfile(image_file):
        return "not an image"

    with open(image_file, "rb") as img_f:
        encoded_string = base64.b64encode(img_f.read())

    return "data:image/%s;base64,%s" % (format, encoded_string)
