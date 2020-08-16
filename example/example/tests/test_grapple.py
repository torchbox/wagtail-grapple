import os

from collections import OrderedDict
from pydoc import locate

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from graphene.test import Client

from wagtail.core.models import Page
from wagtail.documents import get_document_model

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

    def test_propteries_on_example_document_in_wagtail(self):
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
