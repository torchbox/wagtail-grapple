import re
from django.db.models.fields.related_descriptors import (
    ReverseOneToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from graphene.types.definitions import GrapheneInterfaceType
from graphql.language.ast import Field, InlineFragment, FragmentSpread

from modelcluster.fields import ParentalKey

pascal_to_snake = re.compile(r"(?<!^)(?=[A-Z])")


class QueryOptimizer:
    # Fields extracted from AST that the request wants
    qs = None
    schema = None
    model = None
    model_type_map = {}
    query_fields = []

    def __init__(self):
        # Queryset specific lists (for this query)
        self.only_fields = []
        self.select_related_fields = []
        self.prefetch_related_fields = []
        # Future Optimization maps
        self.only_field_types = {}
        self.select_related_types = {}
        self.prefetch_related_types = {}

    @staticmethod
    def query(qs, info):
        # Create new optimizer instance.
        qs_optimizer = QueryOptimizer()
        qs_optimizer.qs = qs
        qs_optimizer.schema = info.schema
        qs_optimizer.model = qs.model
        # Extract what fields the user wants from the AST.
        fields, types = AstExplorer(qs, info).parse_ast()
        qs_optimizer.query_fields = fields
        qs_optimizer.model_type_map = types
        # Sort desired fields in how we preload them.
        qs_optimizer.sort_fields()
        # Add deferred fields to query.
        qs_optimizer.optimise_fields()
        # return the new optimized query
        return qs_optimizer.qs

    # Sort the requested fields, depending on relation to model.
    def sort_fields(self):
        for field_name in self.query_fields or []:
            # Make sure field name is snake not pascal (graphene converts them that way)
            field_name = pascal_to_snake.sub("_", field_name).lower()

            # Ignore typename that causes null error
            if field_name == "__typename":
                continue

            # Support using simple field
            field = getattr(self.model, field_name, None)
            if field:
                self.select_field(field, field_name)
                continue

            # Support more complex sub-selectable fields
            try:
                field_name_prefix, field_name = field_name.split("__", 1)
                nested_field = getattr(self.model, field_name_prefix)
                if nested_field:
                    # Add to query to save recomputing down the line
                    self.select_field(nested_field, field_name, field_name_prefix)
                    continue
            except:
                pass

    def select_field(self, field, field_name, field_name_prefix=None):
        model = self.model_type_map.get(field_name_prefix, None)
        # If link to another model is here then try and parse nested fields
        if isinstance(field, ReverseOneToOneDescriptor):
            # Recursion to load nested fields to support specific pages
            nested_field_name = field_name.split("__")[0]
            nested_field = getattr(model, nested_field_name, None)
            if hasattr(nested_field, "field"):
                return self.select_field(
                    nested_field.field, nested_field_name, field_name_prefix
                )
            else:
                return self.select_field(
                    nested_field, nested_field_name, field_name_prefix
                )

        # Property's or functions can't be selected so we just add id so the query always runs
        if hasattr(model, "id"):
            self.only_fields.append("id")

        # Don't select property functions
        if isinstance(field, property):
            return

        # Don't select method functions
        if callable(field):
            return

        if not getattr(field, "is_relation", False):
            if model:
                # Cache selection for future optimization (query.py)
                existing_fields = self.only_field_types.get(field_name_prefix, [])
                self.only_field_types[field_name_prefix] = [
                    field_name,
                    *existing_fields,
                ]
            else:
                self.only_fields.append(field_name)

        elif field.one_to_many or field.many_to_many or isinstance(field, ParentalKey):
            if model:
                # Cache selection for future optimization (query.py)
                existing_fields = self.prefetch_related_types.get(field_name_prefix, [])
                self.prefetch_related_types[field_name_prefix] = [
                    field_name,
                    *existing_fields,
                ]
            else:
                self.prefetch_related_fields.append(field_name)

        elif field.many_to_one or field.one_to_one:
            if model:
                # Cache selection for future optimization (query.py)
                existing_fields = self.select_related_types.get(field_name_prefix, [])
                self.select_related_types[field_name_prefix] = [
                    field_name,
                    *existing_fields,
                ]
            else:
                self.only_fields.append(field_name)
                self.select_related_fields.append(field_name)

    # Apply order fields to querysets
    def optimise_fields(self):
        self.qs = self.qs.only(*self.only_fields)
        self.qs = self.qs.select_related(*self.select_related_fields)
        self.qs = self.qs.prefetch_related(*self.prefetch_related_fields)

        # Add custom lists to query for use in Specific page optimizer.
        setattr(self.qs.query, "only_field_types", self.only_field_types)
        setattr(self.qs.query, "select_related_types", self.select_related_types)
        setattr(self.qs.query, "prefetch_related_types", self.prefetch_related_types)


class AstExplorer:
    schema = None
    fragments = {}
    model_type_map = {}
    resolve_info = None

    def __init__(self, qs, info):
        self.schema = info.schema
        self.resolve_info = info
        self.fragments = info.fragments

    # Parse AST to find fields
    def parse_ast(self):
        pages_interface = self.get_pages_interface()
        return self.parse_field(pages_interface, None), self.model_type_map

    # Return the pages interface, we only optimise that for now
    def get_pages_interface(self):
        for field in self.resolve_info.field_asts:
            if field.name.value == "page":
                return field
            if field.name.value == "pages":
                return field

    def parse_field(self, field, field_prefix):
        # Don't crash if the field isn't parsable...
        if field is None:
            return

        field_name = field.name.value

        # If field has subset fields
        if field.selection_set:
            field_prefix = field_prefix + "__" + field_name if field_prefix else ""
            return self.parse_selection_set(field.selection_set, field_prefix)

        # Prefix this fieldname with that of it's parent
        if field_prefix:
            return field_prefix + "__" + field.name.value

        # Return fields name
        return field_name

    def parse_selection_set(self, selection_set, field_prefix):
        selections = []
        if selection_set.selections:
            for selection in selection_set.selections:
                selection = self.parse_selection(selection, field_prefix)
                if isinstance(selection, list):
                    selections.extend(selection)
                else:
                    selections.append(selection)

        return selections

    def parse_selection(self, selection, field_prefix):
        if isinstance(selection, InlineFragment):
            return self.parse_inline_fragment(selection, field_prefix)

        if isinstance(selection, FragmentSpread):
            return self.parse_fragment_spread(selection, field_prefix)

        if isinstance(selection, Field):
            return self.parse_field(selection, field_prefix)

    def parse_fragment_spread(self, fragment_spread, field_prefix):
        # Get fragment name.
        fragment_name = fragment_spread.name.value

        # Get fragment type from name and return it parsed.
        fragment_type = self.fragments[fragment_name]
        return self.parse_inline_fragment(
            fragment_type, field_prefix, is_fragment_spread=True
        )

    def parse_inline_fragment(
        self, inline_fragment, field_prefix, is_fragment_spread=False
    ):
        # Get type of inline fragment
        gql_type_name = inline_fragment.type_condition.name.value
        gql_type = self.schema.get_type(gql_type_name)

        # Record what Django model this correlates to
        type_prefix = gql_type_name.lower()
        self.model_type_map[type_prefix] = getattr(
            gql_type.graphene_type._meta, "model", None
        )

        # Function to add the typename to fieldnames
        def prefix_type(field):
            # Don't prefix if the type is an interface
            if not isinstance(gql_type, GrapheneInterfaceType) and field_prefix:
                return field_prefix + "__" + field

            return field

        # Get fields of inline fragment
        selections = []
        if inline_fragment.selection_set:
            selections = self.parse_selection_set(
                inline_fragment.selection_set,
                field_prefix if is_fragment_spread else type_prefix,
            )
            selections = list(map(prefix_type, selections))

        return selections
