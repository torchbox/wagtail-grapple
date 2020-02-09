from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models.query import BaseIterable


def specific(self, *args, **kwargs):
    """
    This efficiently gets all the specific pages for the queryset, using
    the minimum number of queries.

    When the "defer" keyword argument is set to True, only the basic page
    fields will be loaded and all specific fields will be deferred. It
    will still generate a query for each page type though (this may be
    improved to generate only a single query in a future release).
    """
    clone = self._clone()
    clone._iterable_class = DeferredSpecificIterable
    return clone


# Check if desired field exists on model, if so returns them.
def generate_defered_fields(model, fields):
    defer_fields = []
    page_model_satisfies = True
    for field in fields:
        # Simple field names: title, slug
        if hasattr(model, field):
            defer_fields.append(field)

        # Support nested field names: blogpage__title, blogpage__slug
        field_parts = field.split("__")
        if len(field_parts) >= 2:
            model_name = field_parts[0]
            field_name = field_parts[1]
            if model_name == model.__name__.lower() and hasattr(model, field_name):
                page_model_satisfies = False
                defer_fields.append(field_name)

    return defer_fields, page_model_satisfies


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
        pages = specific_model.objects.filter(pk__in=pks)

        # Preload fields in specific models
        if defer:
            # Get deffered fields
            qs_fields, was_deffering = qs.query.deferred_loading
            specific_model_fields, _ = generate_defered_fields(
                specific_model, qs_fields
            )

            # If using .defer or .only
            print(specific_model_fields)
            if was_deffering:
                pages = pages.defer(*specific_model_fields)
            else:
                pages = pages.only(*specific_model_fields)

        # Replace specific models in same sort order
        pages_by_type[content_type] = {page.pk: page for page in pages}

    print("TEST SPECIFIC")

    # Yield all of the pages (specific + generic), in the order they occurred in the original query.
    for pk, content_type in pks_and_types:
        yield pages_by_type[content_type][pk]


class DeferredSpecificIterable(BaseIterable):
    def __iter__(self):
        return specific_iterator(self.queryset, defer=True)
