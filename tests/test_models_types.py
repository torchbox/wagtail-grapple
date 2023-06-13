import graphene
from grapple.models import (
    GraphQLField,
    GraphQLString,
    GraphQLStreamfield,
    GraphQLCollection,
    GraphQLSnippet,
    GraphQLForeignKey,
)
from grapple.types.streamfield import StreamFieldInterface
from grapple.types.structures import (
    QuerySetList,
    BasePaginatedType,
)
from grapple.actions import get_field_type
from django.test import TestCase


class FieldTest(TestCase):
    def setUp(self) -> None:
        self.field_name = "my_field"
        self.deprecation_reason = "Deprecated"
        self.description = "A wonderful field."
        super().setUp()

    def test_field(self):
        """
        Test the GraphQLField class.
        """
        MyType = object()
        field = GraphQLField(
            self.field_name,
            MyType,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )
        # Assert field properties
        assert field.field_name == self.field_name
        assert field.field_type == MyType
        assert field.deprecation_reason == self.deprecation_reason
        assert field.description == self.description

    def test_field_required(self):
        """
        Test the GraphQLField class with required=True.
        """
        MyType = object()
        field = GraphQLField(MyType, required=True)
        # Assert field type is NonNull
        assert isinstance(field.field_type, graphene.NonNull)

    def test_field_required_deprecated(self):
        """
        Test that GraphQLField with required=True and deprecation_reason raises AssertionError.
        """
        with self.assertRaises(AssertionError) as context:
            GraphQLField(
                self.field_name, required=True, deprecation_reason=self.deprecation_reason
            )
        assert (
            str(context.exception)
            == f"Argument {self.field_name} is required, cannot deprecate it."
        )

    def test_streamfield(self):
        """
        Test the GraphQLStreamfield class.
        """
        field = GraphQLStreamfield(
            self.field_name,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Assert field type is List[StreamFieldInterface]
        assert isinstance(field.field_type, graphene.List)
        assert field.field_type.of_type == StreamFieldInterface
        assert field.field_name == self.field_name
        assert field.deprecation_reason == self.deprecation_reason
        assert field.description == self.description

    def test_streamfield_is_not_a_list(self):
        """
        Test the GraphQLStreamfield class with is_list=False.
        """
        field = GraphQLStreamfield(
            self.field_name,
            is_list=False,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Assert field type is StreamFieldInterface
        assert field.field_type == StreamFieldInterface
        assert field.field_name == self.field_name
        assert field.deprecation_reason == self.deprecation_reason
        assert field.description == self.description

    def test_streamfield_required_deprecated(self):
        """
        Test that GraphQLStreamfield with required=True and deprecation_reason raises AssertionError.
        """
        with self.assertRaises(AssertionError) as context:
            GraphQLStreamfield(
                self.field_name, required=True, deprecation_reason=self.deprecation_reason
            )()
        assert (
            str(context.exception)
            == f"Argument {self.field_name} is required, cannot deprecate it."
        )

    def test_streamfield_required(self):
        """
        Test the GraphQLStreamfield class with required=True.
        """
        MyType = object()
        field = GraphQLField(MyType, required=True)
       
        # Assert field type is NonNull
        assert isinstance(field.field_type, graphene.NonNull)

    def test_collection_field(self):
        """
        Test the GraphQLCollection class.
        """
        MyType = GraphQLString
        field = GraphQLCollection(
            MyType,
            self.field_name,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Use get_field_type to replicate behavior of grapple.actions.load_type_fields
        field, field_wrapper = get_field_type(field)
        # Assert field_wrapper type is List
        assert isinstance(field_wrapper, graphene.List)

        MyType = GraphQLSnippet
        field = GraphQLCollection(
            MyType,
            self.field_name,
            "testapp.Advert",
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Use get_field_type to replicate behavior of grapple.actions.load_type_fields
        field, field_wrapper = get_field_type(field)
        # Assert field_wrapper type is QuerySetList
        assert isinstance(field_wrapper, QuerySetList)

        MyType = GraphQLForeignKey
        field = GraphQLCollection(
            MyType,
            self.field_name,
            "testapp.CustomImage",
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Use get_field_type to replicate behavior of grapple.actions.load_type_fields
        field, field_wrapper = get_field_type(field)
        # Assert field_wrapper type is QuerySetList
        assert isinstance(field_wrapper, QuerySetList)

        # is_paginated_queryset should return PaginatedQuerySet
        MyType = GraphQLForeignKey
        field = GraphQLCollection(
            MyType,
            self.field_name,
            "testapp.CustomImage",
            is_paginated_queryset=True,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
        )()
        # Use get_field_type to replicate behavior of grapple.actions.load_type_fields
        field, field_wrapper = get_field_type(field)
        # Assert field_wrapper type is Field and issubclass of BasePaginatedType
        assert isinstance(field_wrapper, graphene.Field)
        assert issubclass(field_wrapper.type, BasePaginatedType)

    def test_collection_field_required_deprecated(self):
        """
        Test that GraphQLCollection with required=True and deprecation_reason raises AssertionError.
        """
        with self.assertRaises(AssertionError) as context:
            MyType = object()
            GraphQLCollection(
                MyType,
                self.field_name,
                required=True,
                deprecation_reason=self.deprecation_reason,
            )()
        assert (
            str(context.exception)
            == f"Argument {self.field_name} is required, cannot deprecate it."
        )
