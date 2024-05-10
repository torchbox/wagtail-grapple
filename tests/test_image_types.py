import wagtail_factories

from django.test import override_settings
from test_grapple import BaseGrappleTestWithIntrospection
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file_svg

from grapple.types.images import rendition_allowed


Image = get_image_model()


class ImageTypesTest(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        cls.example_image = wagtail_factories.ImageFactory(
            title="Example Image", file__filename="grapple-test.png"
        )

    def tearDown(self) -> None:
        for rendition in self.example_image.renditions.all():
            rendition.file.delete(save=False)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.example_image.file.delete(save=False)

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

        data = self.client.execute(query)["data"]["images"]

        self.assertEqual(data[0]["id"], str(self.example_image.id))
        self.assertEqual(
            data[0]["url"],
            "http://localhost:8000" + self.example_image.file.url,
        )
        self.assertEqual(data[0]["url"], data[0]["src"])

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

        data = self.client.execute(query)["data"]["images"]

        self.assertEqual(data[0]["id"], str(self.example_image.id))
        self.assertEqual(
            data[0]["rendition"]["url"],
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
            return f"""
            query ($id: ID!) {{
                image(id: $id) {{
                    rendition({params}) {{
                        url
                    }}
                }}
            }}
            """

        results = self.client.execute(
            get_query(width=100), variables={"id": self.example_image.id}
        )
        self.assertIsNone(results["data"]["image"]["rendition"])
        self.assertEqual(
            results["errors"][0]["message"],
            "Invalid filter specs. Check the `ALLOWED_IMAGE_FILTERS` setting.",
        )

        data = self.client.execute(
            get_query(width=200), variables={"id": self.example_image.id}
        )["data"]["image"]
        self.assertIsNotNone(data["rendition"])
        self.assertIn("width-200", data["rendition"]["url"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 200])
            }
        }
        """

        data = self.client.execute(query, variables={"id": self.example_image.id})[
            "data"
        ]["image"]

        # only the width-200 rendition is allowed
        self.assertNotIn("width-100", data["srcSet"])
        self.assertIn("width-200", data["srcSet"])

    def test_src_set_with_format(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 300], format: "webp")
            }
        }
        """
        data = self.client.execute(query, variables={"id": self.example_image.id})[
            "data"
        ]["image"]
        self.assertIn("width-100.format-webp.webp", data["srcSet"])
        self.assertIn("width-300.format-webp.webp", data["srcSet"])

    def test_src_set_invalid_format(self):
        """
        Ensure that an exception is raised when image format is not of valid type.
        Works with Wagtail versions 5.2 and above. For versions below 5.2 see:
        `test_src_set_invalid_format_wagtail_below_5_2`.
        """

        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100, 300], format: "foobar")
            }
        }
        """

        results = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertEqual(len(results["errors"]), 1)
        self.assertIn("Format must be one of: jpeg", results["errors"][0]["message"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set_disallowed_filter(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
        results = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertEqual("", results["data"]["image"]["srcSet"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200|format-webp"]})
    def test_src_set_allowed_filter(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
        results = self.client.execute(query, variables={"id": self.example_image.id})
        self.assertIn("width-200.format-webp.webp", results["data"]["image"]["srcSet"])

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


class ImageTypesTestWithSVG(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.example_svg_image = wagtail_factories.ImageFactory(
            title="Example SVG Image",
            file=get_test_image_file_svg(filename="grapple-test.svg"),
        )

    def tearDown(self) -> None:
        for rendition in self.example_svg_image.renditions.all():
            rendition.file.delete(save=False)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.example_svg_image.file.delete(save=False)

    def test_schema_for_svg_related_fields_and_arguments(self):
        results = self.introspect_schema_by_type(Image.__name__)
        mapping = {
            field["name"]: field for field in results["data"]["__type"]["fields"]
        }
        rendition_args = {arg["name"]: arg for arg in mapping["rendition"]["args"]}
        src_set_args = {arg["name"]: arg for arg in mapping["srcSet"]["args"]}

        self.assertIn("isSvg", mapping)
        self.assertEqual(mapping["isSvg"]["type"]["kind"], "NON_NULL")
        self.assertEqual(rendition_args["preserveSvg"]["type"]["name"], "Boolean")
        self.assertEqual(
            rendition_args["preserveSvg"]["description"],
            "Prevents raster image operations (e.g. `format-webp`, `bgcolor`, etc.) being applied to SVGs. "
            "More info: https://docs.wagtail.org/en/stable/topics/images.html#svg-images",
        )
        self.assertEqual(src_set_args["preserveSvg"]["type"]["name"], "Boolean")
        self.assertEqual(
            src_set_args["preserveSvg"]["description"],
            "Prevents raster image operations (e.g. `format-webp`, `bgcolor`, etc.) being applied to SVGs. "
            "More info: https://docs.wagtail.org/en/stable/topics/images.html#svg-images",
        )

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

        data = self.client.execute(query, variables={"id": self.example_svg_image.id})[
            "data"
        ]["image"]
        self.assertTrue(data["isSvg"])
        self.assertTrue(data["rendition"]["url"].endswith("test.width-100.svg"))

    def test_svg_rendition_with_raster_format_with_preserve_svg(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                rendition(width: 150, format: "webp") {
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
                "grapple-test.width-150.svg"
            )
        )

    def test_svg_src_set_with_raster_format_with_preserve_svg(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100], format: "webp")
            }
        }
        """

        results = self.client.execute(
            query, variables={"id": self.example_svg_image.id}
        )
        self.assertTrue(
            results["data"]["image"]["srcSet"]
            .split()[0]
            .endswith("grapple-test.width-100.svg")
        )

    def test_svg_rendition_with_raster_format_without_preserve_svg(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                rendition(width: 200, format: "webp", preserveSvg: false) {
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

    def test_svg_src_set_with_raster_format_without_preserve_svg(self):
        query = """
        query ($id: ID!) {
            image(id: $id) {
                srcSet(sizes: [100], format: "webp", preserveSvg: false)
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
                rendition(bgcolor: "fff", format: "webp") {
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
                "grapple-test.original.svg"
            )
        )
