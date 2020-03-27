from collections import defaultdict

from wagtail.core.query import DeferredSpecificIterable
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import BaseIterable


def specific(self, defer=False, *args, **kwargs):
    """
    This efficiently gets all the specific pages for the queryset, using
    the minimum number of queries.

    When the "defer" keyword argument is set to True, only the basic page
    fields will be loaded and all specific fields will be deferred. It
    will still generate a query for each page type though (this may be
    improved to generate only a single query in a future release).
    """
    clone = self._clone()
    if defer:
        clone._iterable_class = GrappleSpecificIterable
    else:
        clone._iterable_class = DeferredSpecificIterable

    return clone


class GrappleSpecificIterable(BaseIterable):
    def __iter__(self):
        return specific_iterator(self.queryset, defer=True)


# Custom version of code from https://github.com/wagtail/wagtail/blob/master/wagtail/core/query.py#L363
def specific_iterator(qs, defer=True):
    """
    This efficiently iterates all the specific pages in a queryset, using
    the minimum number of queries.

    This should be called from ``PageQuerySet.specific``
    """
    pks_and_types = qs.values_list("pk", "content_type")
    pks_by_type = defaultdict(list)
    for pk, content_type in pks_and_types:
        pks_by_type[content_type].append(pk)

    # Content types are cached by ID, so this will not run any queries.
    content_types = {pk: ContentType.objects.get_for_id(pk) for _, pk in pks_and_types}

    # Get the specific instances of all pages, one model class at a time.
    pages_by_type = {}
    for content_type, pks in pks_by_type.items():
        # look up model class for this content type, falling back on the original
        # model (i.e. Page) if the more specific one is missing
        specific_model = content_types[content_type].model_class() or qs.model
        specific_model_name = specific_model.__name__.lower()

        # Get deffered fields (.only/.deffer)
        only_fields, _ = qs.query.deferred_loading
        only_fields_specific = getattr(qs.query, "only_field_types", {}).get(
            specific_model_name, []
        )
        select_related_fields = getattr(qs.query, "select_related_types", {}).get(
            specific_model_name, []
        )
        prefetch_related_fields = getattr(qs.query, "prefetch_related_types", {}).get(
            specific_model_name, []
        )

        # If no fields of this model requested then don't query specific
        if not only_fields:
            pages_by_type[content_type] = None
            continue

        # Query pages
        pages = specific_model.objects.filter(pk__in=pks)
        # Defer all fields apart from those required
        pages = pages.only(*only_fields, *only_fields_specific)
        # Apply select_related fields (passed down from optimizer.py)
        pages = pages.select_related(*select_related_fields)
        # Apply prefetch_related fields (passed down from optimizer.py)
        pages = pages.prefetch_related(*prefetch_related_fields)

        # Replace specific models in same sort order
        pages_by_type[content_type] = {page.pk: page for page in pages}

    # Yield all of the pages (specific + generic), in the order they occurred in the original query.
    for pk, content_type in pks_and_types:
        if pages_by_type[content_type]:
            yield pages_by_type[content_type][pk]
