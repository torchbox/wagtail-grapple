from collections import OrderedDict
from pydoc import locate

from django.conf import settings
from django.test import TestCase, override_settings

from graphene.test import Client

from wagtail.core.models import Page

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
