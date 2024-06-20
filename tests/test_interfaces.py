import os

from unittest import skipIf, skipUnless

from django.test import override_settings, tag
from test_grapple import BaseGrappleTestWithIntrospection
from testapp.factories import BlogPageFactory, CustomInterfaceBlockFactory
from testapp.interfaces import CustomInterface

from grapple.types.pages import PageInterface, get_page_interface


@skipIf(
    os.getenv("DJANGO_SETTINGS_MODULE") == "settings_custom_page_interface",
    "Cannot run with settings_custom_page_interface",
)
class InterfacesTestCase(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.blog_page = BlogPageFactory(
            body=[
                ("custom_interface_block", CustomInterfaceBlockFactory()),
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

    @override_settings(GRAPPLE={"PAGE_INTERFACE": "testapp.interfaces.CustomInterface"})
    def test_get_page_interface_with_custom_page_interface(self):
        self.assertIs(get_page_interface(), CustomInterface)

    def test_streamfield_block_with_custom_interface(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    body {
                        blockType
                        ...on CustomInterface {
                            customText
                        }
                    }
                }
            }
        }
        """
        results = self.client.execute(query, variables={"id": self.blog_page.id})
        body = results["data"]["page"]["body"]

        for block in body:
            if block["blockType"] == "CustomInterfaceBlock":
                self.assertRegex(
                    block["customText"], r"^Block with custom interface \d+$"
                )
                return

        self.fail("Query by interface didn't match anything")

    def test_schema_for_streamfield_block_with_custom_interface(self):
        results = self.introspect_schema_by_type("CustomInterfaceBlock")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "CustomInterface"}, {"name": "StreamFieldInterface"}],
        )

    def test_schema_for_page_with_graphql_interface(self):
        results = self.introspect_schema_by_type("AuthorPage")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "CustomInterface"}, {"name": "PageInterface"}],
        )

    def test_schema_for_snippet_with_graphql_interface(self):
        results = self.introspect_schema_by_type("Advert")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "CustomInterface"}],
        )

    def test_schema_for_django_model_with_graphql_interfaces(self):
        results = self.introspect_schema_by_type("SimpleModel")
        self.assertListEqual(
            sorted(results["data"]["__type"]["interfaces"], key=lambda x: x["name"]),
            [{"name": "CustomInterface"}],
        )


@tag("needs-custom-settings")
@skipUnless(
    os.getenv("DJANGO_SETTINGS_MODULE") == "settings_custom_page_interface",
    "Needs settings_custom_page_interface",
)
class CustomPageInterfaceTestCase(BaseGrappleTestWithIntrospection):
    def test_schema_with_custom_page_interface(self):
        results = self.introspect_schema_by_type("BlogPage")
        self.assertListEqual(
            results["data"]["__type"]["interfaces"], [{"name": "CustomInterface"}]
        )
