import shutil

import wagtail_factories

from django.conf import settings
from django.test import override_settings
from test_grapple import BaseGrappleTestWithIntrospection
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
            return """
            {
                image(id: %d) {
                    rendition(%s) {
                        url
                    }
                }
            }
            """ % (
                self.example_image.id,
                params,
            )

        executed = self.client.execute(get_query(width=100))
        self.assertIsNone(executed["data"]["image"]["rendition"])

        executed = self.client.execute(get_query(width=200))
        self.assertIsNotNone(executed["data"]["image"]["rendition"])
        self.assertIn("width-200", executed["data"]["image"]["rendition"]["url"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set(self):
        query = (
            """
        {
            image(id: %d) {
                srcSet(sizes: [100, 200])
            }
        }
        """
            % self.example_image.id
        )

        executed = self.client.execute(query)

        # only the width-200 rendition is allowed
        self.assertNotIn("width-100", executed["data"]["image"]["srcSet"])
        self.assertIn("width-200", executed["data"]["image"]["srcSet"])

    def test_src_set_with_format(self):
        query = (
            """
        {
            image(id: %d) {
                srcSet(sizes: [100, 300], format: "webp")
            }
        }
        """
            % self.example_image.id
        )
        executed = self.client.execute(query)
        self.assertIn("width-100.format-webp.webp", executed["data"]["image"]["srcSet"])
        self.assertIn("width-300.format-webp.webp", executed["data"]["image"]["srcSet"])

    def test_src_set_invalid_format(self):
        query = (
            """
        {
            image(id: %d) {
                srcSet(sizes: [100, 300], format: "foobar")
            }
        }
        """
            % self.example_image.id
        )
        executed = self.client.execute(query)
        self.assertEqual(len(executed["errors"]), 1)
        self.assertIn("Format must be either 'jpeg'", executed["errors"][0]["message"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set_disallowed_filter(self):
        query = (
            """
        {
            image(id: %d) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
            % self.example_image.id
        )
        executed = self.client.execute(query)
        self.assertEqual("", executed["data"]["image"]["srcSet"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200|format-webp"]})
    def test_src_set_allowed_filter(self):
        query = (
            """
        {
            image(id: %d) {
                srcSet(sizes: [200], format: "webp")
            }
        }
        """
            % self.example_image.id
        )
        executed = self.client.execute(query)
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
