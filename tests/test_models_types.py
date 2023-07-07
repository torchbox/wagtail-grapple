import graphene
from django.test import TestCase

from grapple.actions import get_field_type
from grapple.exceptions import IllegalDeprecation
from grapple.models import (
    GraphQLCollection,
    GraphQLField,
    GraphQLForeignKey,
    GraphQLSnippet,
    GraphQLStreamfield,
    GraphQLString,
)
from grapple.types.streamfield import StreamFieldInterface
from grapple.types.structures import BasePaginatedType, QuerySetList


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
        self.assertEqual(field.field_name, self.field_name)
        self.assertEqual(field.field_type, MyType)
        self.assertEqual(field.deprecation_reason, self.deprecation_reason)
        self.assertEqual(field.description, self.description)

    def test_field_required(self):
        """
        Test the GraphQLField class with required=True.
        """
        MyType = object()
        field = GraphQLField(MyType, required=True)
        # Assert field type is NonNull
        self.assertIsInstance(field.field_type, graphene.NonNull)

    def test_field_required_deprecated(self):
        """
        Test that GraphQLField with required=True and deprecation_reason raises IllegalDeprecation.
        """
        with self.assertRaises(IllegalDeprecation):
            GraphQLField(
                self.field_name,
                required=True,
                deprecation_reason=self.deprecation_reason,
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
        self.assertIsInstance(field.field_type, graphene.List)
        self.assertEqual(field.field_type.of_type, StreamFieldInterface)
        self.assertEqual(field.field_name, self.field_name)
        self.assertEqual(field.deprecation_reason, self.deprecation_reason)
        self.assertEqual(field.description, self.description)

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
        self.assertEqual(field.field_type, StreamFieldInterface)
        self.assertEqual(field.field_name, self.field_name)
        self.assertEqual(field.deprecation_reason, self.deprecation_reason)
        self.assertEqual(field.description, self.description)

    def test_streamfield_required_deprecated(self):
        """
        Test that GraphQLStreamfield with required=True and deprecation_reason raises IllegalDeprecation.
        """
        with self.assertRaises(IllegalDeprecation):
            GraphQLStreamfield(
                self.field_name,
                required=True,
                deprecation_reason=self.deprecation_reason,
            )()

    def test_streamfield_required(self):
        """
        Test the GraphQLStreamfield class with required=True.
        """
        MyType = object()
        field = GraphQLField(MyType, required=True)

        # Assert field type is NonNull
        self.assertIsInstance(field.field_type, graphene.NonNull)

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
        self.assertIsInstance(field_wrapper, graphene.List)

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
        self.assertIsInstance(field_wrapper, QuerySetList)

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
        self.assertIsInstance(field_wrapper, QuerySetList)

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
        self.assertIsInstance(field_wrapper, graphene.Field)
        self.assertTrue(issubclass(field_wrapper.type, BasePaginatedType))

    def test_collection_field_required_deprecated(self):
        """
        Test that GraphQLCollection with required=True and deprecation_reason raises IllegalDeprecation.
        """
        with self.assertRaises(IllegalDeprecation):
            MyType = object()
            GraphQLCollection(
                MyType,
                self.field_name,
                required=True,
                deprecation_reason=self.deprecation_reason,
            )()
