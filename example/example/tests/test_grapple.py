from collections import OrderedDict
from pydoc import locate

from django.conf import settings
from django.test import TestCase

from graphene.test import Client

from wagtail.core.models import Page

SCHEMA = locate(settings.GRAPHENE['SCHEMA'])


class BaseGrappleTest(TestCase):
    def setUp(self):
        self.client = Client(SCHEMA)


class PagesTest(BaseGrappleTest):
    def test_pages(self):
        query = '''
        {
            pages {
                title
            }
        }
        '''

        executed = self.client.execute(query)

        self.assertEquals(type(executed['data']), OrderedDict)
        self.assertEquals(type(executed['data']['pages']), list)
        self.assertEquals(type(executed['data']['pages'][0]), OrderedDict)

        pages = Page.objects.all()

        self.assertEquals(len(executed['data']['pages']), pages.count())
