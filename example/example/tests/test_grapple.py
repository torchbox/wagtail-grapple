import os

from collections import OrderedDict
from pydoc import locate

import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from graphene.test import Client

from wagtail.core.models import Page
from wagtail.documents import get_document_model
from wagtail.images import get_image_model

import wagtail_factories

from grapple.schema import create_schema

SCHEMA = locate(settings.GRAPHENE["SCHEMA"])


class BaseGrappleTest(TestCase):
    def setUp(self):
        self.client = Client(SCHEMA)


class PagesTest(BaseGrappleTest):
    def test_pages(self):
        query = """
        {
            pages {
                title
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(type(executed["data"]), OrderedDict)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), OrderedDict)

        pages = Page.objects.all()

        self.assertEquals(len(executed["data"]["pages"]), pages.count())


@override_settings(GRAPPLE_AUTO_CAMELCASE=False)
class DisableAutoCamelCaseTest(TestCase):
    def setUp(self):
        schema = create_schema()
        self.client = Client(schema)

    def test_disable_auto_camel_case(self):
        query = """
        {
            pages {
                title
                url_path
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(type(executed["data"]), OrderedDict)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), OrderedDict)
        self.assertEquals(type(executed["data"]["pages"][0]["title"]), str)
        self.assertEquals(type(executed["data"]["pages"][0]["url_path"]), str)

        pages = Page.objects.all()

        self.assertEquals(len(executed["data"]["pages"]), pages.count())


class ImagesTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.image_model = get_image_model()
        self.assertEqual(self.image_model.objects.all().count(), 0)
        self.example_image = wagtail_factories.ImageFactory(
            title="Example Image",
        )
        self.example_image.full_clean()
        self.example_image.save()
        self.assertEqual(self.image_model.objects.all().count(), 1)

    def test_properties_on_saved_example_image(self):
        example_img = self.image_model.objects.first()

        self.assertEqual(example_img.id, 1)
        self.assertEqual(example_img.title, "Example Image")

    def test_query_image_src(self):
        query = """
        {
            images {
                id
                src
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(
            executed["data"]["images"][0]["id"],
            "1",
        )
        self.assertEquals(
            executed["data"]["images"][0]["src"],
            "http://localhost:8000" + self.example_image.file.url,
        )

    def tearDown(self):
        example_image_path = self.example_image.file.path
        self.example_image.delete()
        os.remove(example_image_path)


class DocumentsTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.document_model = get_document_model()
        self.assertEqual(self.document_model.objects.all().count(), 0)

        uploaded_file = SimpleUploadedFile("example.txt", b"Hello world!")
        self.example_document = self.document_model(
            title="Example File",
            file=uploaded_file,
        )
        self.example_document.full_clean()
        self.example_document.save()
        self.example_document.get_file_hash()
        self.example_document.get_file_size()
        self.assertEqual(self.document_model.objects.all().count(), 1)

    def test_propteries_on_saved_example_document(self):
        example_doc = self.document_model.objects.first()

        self.assertEqual(example_doc.id, 1)
        self.assertEqual(example_doc.title, "Example File")

        example_doc.file.seek(0)

        self.assertEqual(example_doc.file.readline(), b"Hello world!")

        self.assertNotEqual(example_doc.file_hash, "")
        self.assertNotEqual(example_doc.file_size, None)

    def test_minimal_documents_query(self):
        query = """
        {
            documents {
                id
            }
        }
        """

        executed = self.client.execute(query)

        documents = self.document_model.objects.all()

        self.assertEquals(
            len(executed["data"]["documents"]),
            documents.count(),
        )
        self.assertEquals(
            executed["data"]["documents"][0]["id"],
            str(self.example_document.id),
        )

    def test_file_field(self):
        query = """
        {
            documents {
                id
                file
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(
            executed["data"]["documents"][0]["file"],
            self.example_document.file.name,
        )

    def test_file_hash_field(self):
        query = """
        {
            documents {
                id
                fileHash
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(
            executed["data"]["documents"][0]["fileHash"],
            self.example_document.file_hash,
        )

    def test_file_size_field(self):
        query = """
        {
            documents {
                id
                fileSize
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(
            executed["data"]["documents"][0]["fileSize"],
            self.example_document.file_size,
        )

    def tearDown(self):
        self.example_document.file.delete()
