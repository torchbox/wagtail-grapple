import shutil

import wagtail_factories

from django.conf import settings
from django.test import override_settings
from test_grapple import BaseGrappleTest, BaseGrappleTestWithIntrospection
from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.images import get_image_model

from grapple.types.images import rendition_allowed


class ImageTypesTest(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        cls.image_model = get_image_model()
        cls.example_image = wagtail_factories.ImageFactory(title="Example Image")
        cls.example_image.full_clean()
        cls.example_image.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_properties_on_saved_example_image(self):
        example_img = self.image_model.objects.first()

        self.assertEqual(example_img.id, self.example_image.id)
        self.assertEqual(example_img.title, "Example Image")

    def test_query_url_field(self):
        query = """
        {
            images {
                id
                url
                src
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEqual(
            executed["data"]["images"][0]["id"], str(self.example_image.id)
        )
        self.assertEqual(
            executed["data"]["images"][0]["url"],
            "http://localhost:8000" + self.example_image.file.url,
        )
        self.assertEqual(
            executed["data"]["images"][0]["url"], executed["data"]["images"][0]["src"]
        )

    def test_query_rendition_url_field(self):
        query = """
        {
            images {
                id
                rendition(width: 200) {
                    url
                }
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEqual(
            executed["data"]["images"][0]["id"], str(self.example_image.id)
        )
        self.assertEqual(
            executed["data"]["images"][0]["rendition"]["url"],
            self.example_image.get_rendition("width-200").full_url,
        )

    def test_renditions(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                rendition(width: 100) {
                    url
                    customRenditionProperty
                }
            }
        }
        """

        executed = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertIn("width-100", executed["data"]["image"]["rendition"]["url"])
        self.assertIn(
            "Rendition Model!",
            executed["data"]["image"]["rendition"]["customRenditionProperty"],
        )

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_renditions_with_allowed_image_filters_restrictions(self):
        def get_query(**kwargs):
            params = ",".join([f"{key}: {value}" for key, value in kwargs.items()])
            return (
                """
            query ($id: ID!) {
                image(id: $id) {
                    rendition(%s) {
                        url
                    }
                }
            }
            """
                % params
            )

        executed = self.client.execute(
            get_query(width=100), variables={"id": self.example_image.id}
        )
        self.assertIsNone(executed["data"]["image"]["rendition"])

        executed = self.client.execute(
            get_query(width=200), variables={"id": self.example_image.id}
        )
        self.assertIsNotNone(executed["data"]["image"]["rendition"])
        self.assertIn("width-200", executed["data"]["image"]["rendition"]["url"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 200])
            }
        }
        """

        executed = self.client.execute(query, variables={"id": self.example_image.id})

        # only the width-200 rendition is allowed
        self.assertNotIn("width-100", executed["data"]["image"]["srcSet"])
        self.assertIn("width-200", executed["data"]["image"]["srcSet"])

    def test_src_set_with_format(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 300], format: "webp")
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertIn("width-100.format-webp.webp", executed["data"]["image"]["srcSet"])
        self.assertIn("width-300.format-webp.webp", executed["data"]["image"]["srcSet"])

    def test_src_set_invalid_format(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 300], format: "foobar")
            }
        }
        """

        executed = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertEqual(len(executed["errors"]), 1)
        self.assertIn("Format must be either 'jpeg'", executed["errors"][0]["message"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set_disallowed_filter(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertEqual("", executed["data"]["image"]["srcSet"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200|format-webp"]})
    def test_src_set_allowed_filter(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertIn("width-200.format-webp.webp", executed["data"]["image"]["srcSet"])

    def test_rendition_allowed_method(self):
        self.assertTrue(rendition_allowed("width-100"))
        with override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]}):
            self.assertFalse(rendition_allowed("width-100"))
            self.assertTrue(rendition_allowed("width-200"))

        with override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": []}):
            self.assertFalse(rendition_allowed("width-100"))
            self.assertFalse(rendition_allowed("fill-100x100"))

    def test_src_set_num_queries(self):
        sizes = [360, 720, 1024]
        filters = [f"width-{size}" for size in sizes]

        def get_renditions(image):
            for img_filter in filters:
                image.get_rendition(img_filter)

        # Generate renditions for each filter in the filters list for all images
        get_renditions(self.example_image)
        for i in range(4):
            get_renditions(wagtail_factories.ImageFactory(title=f"Image {i}"))

        query = """
        {
            images {
                srcSet(sizes: [360, 720, 1024])
            }
        }
        """

        with self.assertNumQueries(2):
            self.client.execute(query)

    def test_schema_for_svg_related_fields_and_arguments(self):
        results = self.query_schema_by_type(self.image_model.__name__)
        mapping = {
            field["name"]: field for field in results["data"]["__type"]["fields"]
        }
        rendition_args = {arg["name"]: arg for arg in mapping["rendition"]["args"]}

        if WAGTAIL_VERSION >= (5, 0):
            self.assertIn("isSvg", mapping)
            self.assertEqual(mapping["isSvg"]["type"]["kind"], "NON_NULL")
            self.assertEqual(rendition_args["preserveSvg"]["type"]["name"], "Boolean")
            self.assertEqual(
                rendition_args["preserveSvg"]["description"],
                "Restrict the operations applied to an SVG image to only those that do not require rasterisation",
            )
        else:
            self.assertNotIn("isSvg", mapping)
            self.assertNotIn("preserveSvg", rendition_args)


if WAGTAIL_VERSION >= (5, 0):
    from wagtail.images.tests.utils import get_test_image_file_svg

    class ImageTypesTestWithSVG(BaseGrappleTest):
        @classmethod
        def setUpTestData(cls):
            super().setUpTestData()
            cls.example_svg_image = wagtail_factories.ImageFactory(
                title="Example SVG Image", file=get_test_image_file_svg()
            )

        @classmethod
        def tearDownClass(cls):
            super().tearDownClass()
            shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

        def test_svg_rendition(self):
            query = """
            query ($id: ID!) {
                image(id: $id) {
                    isSvg
                    rendition(width: 100) {
                        url
                    }
                }
            }
            """

            results = self.client.execute(
                query, variables={"id": self.example_svg_image.id}
            )
            self.assertTrue(results["data"]["image"]["isSvg"])
            self.assertTrue(
                results["data"]["image"]["rendition"]["url"].endswith(
                    "test.width-100.svg"
                )
            )

        def test_svg_rendition_with_raster_format_with_preserve_svg(self):
            query = """
            query ($id: ID!) {
                image(id: $id) {
                    rendition(width: 150, format: "webp", preserveSvg: true) {
                        url
                    }
                }
            }
            """

            results = self.client.execute(
                query, variables={"id": self.example_svg_image.id}
            )
            self.assertTrue(
                results["data"]["image"]["rendition"]["url"].endswith(
                    "test.width-150.svg"
                )
            )

        def test_svg_rendition_with_raster_format_without_preserve_svg(self):
            query = """
            query ($id: ID!) {
                image(id: $id) {
                    rendition(width: 200, format: "webp") {
                        url
                    }
                }
            }
            """

            results = self.client.execute(
                query, variables={"id": self.example_svg_image.id}
            )
            self.assertEqual(
                results["errors"][0]["message"],
                "'SvgImage' object has no attribute 'save_as_webp'",
            )

        def test_svg_rendition_with_filters_passed_through_to_svg_safe_spec(self):
            # bgcolor is not one of the allowed filters, so we should end with an empty filter spec
            query = """
            query ($id: ID!) {
                image(id: $id) {
                    rendition(bgcolor: "fff", format: "webp", preserveSvg: true) {
                        url
                    }
                }
            }
            """

            results = self.client.execute(
                query, variables={"id": self.example_svg_image.id}
            )
            self.assertIsNone(results["data"]["image"]["rendition"])
