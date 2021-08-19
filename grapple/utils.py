import os
import base64
from contextlib import contextmanager

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from wagtail.search.index import class_is_indexed
from wagtail.search.models import Query
from wagtail.search.backends import get_search_backend


from willow.image import Image as WillowImage

from .types.structures import BasePaginatedType, PaginationType
from .settings import grapple_settings


def resolve_queryset(
    qs,
    info,
    limit=None,
    offset=None,
    search_query=None,
    id=None,
    order=None,
    collection=None,
    **kwargs
):
    """
    Add limit, offset and search capabilities to the query. This contains
    argument names used by
    :class:`~grapple.types.structures.QuerySetList`.
    :param qs: The query set to be modified.
    :param info: The Graphene info object.
    :param limit: Limit number of objects in the QuerySet.
    :type limit: int
    :param id: Filter by the primary key.
    :type id: int
    :param offset: Omit a number of objects from the beginning of the query set
    :type offset: int
    :param search_query: Using Wagtail search, exclude objects that do not match
                         the search query.
    :type search_query: str
    :param order: Order the query set using the Django QuerySet order_by format.
    :type order: str
    :param collection: Use Wagtail's collection id to filter images or documents
    :type collection: int
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

        if grapple_settings.ADD_SEARCH_HIT:
            query = Query.get(search_query)
            query.add_hit()

        return get_search_backend().search(search_query, qs)

    if order is not None:
        qs = qs.order_by(*map(lambda x: x.strip(), order.split(",")))

    if collection is not None:
        try:
            qs.model._meta.get_field("collection")
            qs = qs.filter(collection=collection)
        except:
            pass

    if limit is not None:
        limit = min(
            int(limit or grapple_settings.PAGE_SIZE), grapple_settings.MAX_PAGE_SIZE
        )
        qs = qs[offset : limit + offset]

    return qs


def get_paginated_result(qs, page, per_page):
    """
    Returns a paginated result.
    """
    paginator = Paginator(qs, per_page)

    try:
        # If the page exists and the page is an int
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # If the page is not an int; show the first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If the page is out of range (too high most likely)
        # Then return the last page
        page_obj = paginator.page(paginator.num_pages)

    return BasePaginatedType(
        items=page_obj.object_list,
        pagination=PaginationType(
            total=paginator.count,
            count=len(page_obj.object_list),
            per_page=per_page,
            current_page=page_obj.number,
            prev_page=page_obj.previous_page_number()
            if page_obj.has_previous()
            else None,
            next_page=page_obj.next_page_number() if page_obj.has_next() else None,
            total_pages=paginator.num_pages,
        ),
    )


def resolve_paginated_queryset(
    qs, info, page=None, per_page=None, search_query=None, id=None, order=None, **kwargs
):
    """
    Add page, per_page and search capabilities to the query. This contains
    argument names used by
    :function:`~grapple.types.structures.PaginatedQuerySet`.
    :param qs: The query set to be modified.
    :param info: The Graphene info object.
    :param page: Page of resulting objects to return from the QuerySet.
    :type page: int
    :param id: Filter by the primary key.
    :type id: int
    :param per_page: The maximum number of items to include on a page.
    :type per_page: int
    :param search_query: Using Wagtail search, exclude objects that do not match
                         the search query.
    :type search_query: str
    :param order: Order the query set using the Django QuerySet order_by format.
    :type order: str
    """
    page = int(page or 1)
    per_page = min(
        int(per_page or grapple_settings.PAGE_SIZE), grapple_settings.MAX_PAGE_SIZE
    )

    if id is not None:
        qs = qs.filter(pk=id)
    else:
        qs = qs.all()

    if id is None and search_query:
        # Check if the queryset is searchable using Wagtail search.
        if not class_is_indexed(qs.model):
            raise TypeError("This data type is not searchable by Wagtail.")

        if grapple_settings.ADD_SEARCH_HIT:
            query = Query.get(search_query)
            query.add_hit()

        results = get_search_backend().search(search_query, qs)

        return get_paginated_result(results, page, per_page)

    if order is not None:
        qs = qs.order_by(*map(lambda x: x.strip(), order.split(",")))

    return get_paginated_result(qs, page, per_page)


def get_media_item_url(cls):
    url = ""
    if hasattr(cls, "url"):
        url = cls.url
    elif hasattr(cls, "file"):
        url = cls.file.url

    if url[0] == "/":
        return settings.BASE_URL + url
    return url


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


class SourceImageIOError(IOError):
    """
    Custom exception to distinguish IOErrors that were thrown while opening the source image
    """

    pass


@contextmanager
def get_willow_image(rendition):
    """
    This method was borrowed from wagtail.images.models.

    A PR is opened that will bring this to the AbstractRendition model https://github.com/wagtail/wagtail/pull/7444
    Once it is merged, the method below can be removed and the code in grapple.types.images
    can take advantage of rendition.get_willow_image() method.
    """
    with open_file(rendition) as image_file:
        yield WillowImage.open(image_file)


def is_stored_locally(rendition):
    """
    Returns True if the image is hosted on the local filesystem

    This method was borrowed from wagtail.images.models.
    See get_willow_image method comment for details.
    """
    try:
        rendition.file.path
        return True
    except NotImplementedError:
        return False


@contextmanager
def open_file(rendition):
    """
    This method was borrowed from wagtail.renditions.models.

    See get_willow_rendition method comment for details.
    """
    # Open file if it is closed
    close_file = False
    try:
        rendition_file = rendition.file

        if rendition.file.closed:
            # Reopen the file
            if is_stored_locally(rendition):
                rendition.file.open("rb")
            else:
                # Some external storage backends don't allow reopening
                # the file. Get a fresh file instance. #1397
                storage = rendition._meta.get_field("file").storage
                rendition_file = storage.open(rendition.file.name, "rb")

            close_file = True
    except IOError as e:
        # re-throw this as a SourceImageIOError so that calling code can distinguish
        # these from IOErrors elsewhere in the process
        raise SourceImageIOError(str(e))

    # Seek to beginning
    rendition_file.seek(0)

    try:
        yield rendition_file
    finally:
        if close_file:
            rendition_file.close()
