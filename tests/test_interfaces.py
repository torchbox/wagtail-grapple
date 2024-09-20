import os

from unittest import skipIf, skipUnless

from django.test import override_settings, tag
from test_grapple import BaseGrappleTestWithIntrospection
from testapp.factories import AdditionalInterfaceBlockFactory, BlogPageFactory
from testapp.interfaces import CustomPageInterface, CustomSnippetInterface

from grapple.types.interfaces import (
    PageInterface,
    get_page_interface,
    get_snippet_interface,
)


@skipIf(
    os.getenv("DJANGO_SETTINGS_MODULE") == "settings_custom_interfaces",
    "Cannot run with settings_custom_interfaces",
)
class InterfacesTestCase(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.blog_page = BlogPageFactory(
            body=[
                ("additional_interface_block", AdditionalInterfaceBlockFactory()),
            ],
            parent=cls.home,
        )

    def test_get_page_interface_with_default_page_interface(self):
        self.assertIs(get_page_interface(), PageInterface)

    def test_schema_with_default_page_interface(self):
        results = self.introspect_schema_by_type("BlogPage")
        self.assertListEqual(
            results["data"]["__type"]["interfaces"], [{"name": "PageInterface"}]
        )

    @override_settings(
        GRAPPLE={"PAGE_INTERFACE": "testapp.interfaces.CustomPageInterface"}
    )
    def test_get_page_interface_with_custom_page_interface(self):
        self.assertIs(get_page_interface(), CustomPageInterface)

    @override_settings(
        GRAPPLE={"SNIPPET_INTERFACE": "testapp.interfaces.CustomSnippetInterface"}
    )
    def test_get_snippet_interface_with_custom_page_interface(self):
        self.assertIs(get_snippet_interface(), CustomSnippetInterface)

    def test_streamfield_block_with_additional_interface(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    body {
                        blockType
                        ...on AdditionalInterface {
                            additionalText
                        }
                    }
                }
            }
        }
        """
        results = self.client.execute(query, variables={"id": self.blog_page.id})
        body = results["data"]["page"]["body"]

        for block in body:
            if block["blockType"] == "AdditionalInterfaceBlock":
                self.assertRegex(
                    block["additionalText"], r"^Block with additional interface \d+$"
                )
                return

        self.fail("Query by interface didn't match anything")

    def test_schema_for_streamfield_block_with_additional_interface(self):
        results = self.introspect_schema_by_type("AdditionalInterfaceBlock")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "AdditionalInterface"}, {"name": "StreamFieldInterface"}],
        )

    def test_schema_for_page_with_graphql_interface(self):
        results = self.introspect_schema_by_type("AuthorPage")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "AdditionalInterface"}, {"name": "PageInterface"}],
        )

    def test_schema_for_snippet_with_graphql_interface(self):
        results = self.introspect_schema_by_type("Advert")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "AdditionalInterface"}, {"name": "SnippetInterface"}],
        )

    def test_schema_for_django_model_with_graphql_interfaces(self):
        results = self.introspect_schema_by_type("SimpleModel")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "AdditionalInterface"}],
        )


@tag("needs-custom-settings")
@skipUnless(
    os.getenv("DJANGO_SETTINGS_MODULE") == "settings_custom_interfaces",
    "Needs settings_custom_interfaces",
)
class CustomInterfacesTestCase(BaseGrappleTestWithIntrospection):
    def test_schema_with_custom_page_interface(self):
        results = self.introspect_schema_by_type("BlogPage")
        self.assertListEqual(
            results["data"]["__type"]["interfaces"], [{"name": "CustomPageInterface"}]
        )

    def test_schema_with_custom_snippet_interface(self):
        results = self.introspect_schema_by_type("Person")
        self.assertListEqual(
            results["data"]["__type"]["interfaces"],
            [{"name": "CustomSnippetInterface"}],
        )
