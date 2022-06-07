import inspect
import os
import sys
from unittest.mock import patch

import wagtail_factories

from grapple.types.images import rendition_allowed

if sys.version_info >= (3, 7):
    from builtins import dict as dict_type
else:
    from collections import OrderedDict as dict_type

from pydoc import locate

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from graphene.test import Client
from home.factories import BlogPageFactory
from home.models import HomePage

try:
    from wagtail.models import Page, Site
except ImportError:
    from wagtail.core.models import Page, Site
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtailmedia.models import get_media_model

from grapple.schema import create_schema

SCHEMA = locate(settings.GRAPHENE["SCHEMA"])
MIDDLEWARE_OBJECTS = [
    locate(middleware) for middleware in settings.GRAPHENE["MIDDLEWARE"]
]
MIDDLEWARE = [item() if inspect.isclass(item) else item for item in MIDDLEWARE_OBJECTS]


class BaseGrappleTest(TestCase):
    def setUp(self):
        self.client = Client(SCHEMA, middleware=MIDDLEWARE)
        self.home = HomePage.objects.first()


class BaseGrappleTestWithIntrospection(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        query = """
        query availableQueries {
          __schema {
            queryType {
              fields{
                name
                type {
                  kind
                  ofType {
                    name
                    kind
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                  }
                }
              }
            }
          }
        }
        """
        executed = self.client.execute(query)
        self.available_queries = executed["data"]["__schema"]["queryType"]["fields"]


class PagesTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.blog_post = BlogPageFactory(parent=self.home)

    def test_pages(self):
        query = """
        {
            pages {
                id
                title
                contentType
                pageType
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), dict_type)

        pages_data = executed["data"]["pages"]
        self.assertEquals(pages_data[0]["contentType"], "home.HomePage")
        self.assertEquals(pages_data[0]["pageType"], "HomePage")
        self.assertEquals(pages_data[1]["contentType"], "home.BlogPage")
        self.assertEquals(pages_data[1]["pageType"], "BlogPage")

        pages = Page.objects.filter(depth__gt=1)
        self.assertEquals(len(executed["data"]["pages"]), pages.count())

    @override_settings(GRAPPLE={"PAGE_SIZE": 1, "MAX_PAGE_SIZE": 1})
    def test_pages_limit(self):
        query = """
        {
            pages(limit: 5) {
                id
                title
                contentType
                pageType
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), dict_type)

        pages_data = executed["data"]["pages"]
        self.assertEquals(pages_data[0]["contentType"], "home.HomePage")
        self.assertEquals(pages_data[0]["pageType"], "HomePage")
        self.assertEquals(len(executed["data"]["pages"]), 1)

    def test_pages_in_site(self):
        query = """
        {
            pages(inSite: true) {
                title
                contentType
                pageType
            }
        }
        """

        request = self.factory.get("/")
        executed = self.client.execute(query, context_value=request)

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), dict_type)

        site = Site.find_for_request(request)
        pages = Page.objects.in_site(site)

        self.assertEquals(len(executed["data"]["pages"]), pages.count())

    def test_pages_content_type_filter(self):
        query = """
        query($content_type: String) {
            pages(contentType: $content_type) {
                id
                title
                contentType
                pageType
            }
        }
        """

        results = self.client.execute(
            query, variables={"content_type": "home.HomePage"}
        )
        data = results["data"]["pages"]
        self.assertEquals(len(data), 1)
        self.assertEqual(int(data[0]["id"]), self.home.id)

        another_post = BlogPageFactory(parent=self.home)
        results = self.client.execute(
            query, variables={"content_type": "home.BlogPage"}
        )
        data = results["data"]["pages"]
        self.assertEqual(len(data), 2)
        self.assertListEqual(
            [int(p["id"]) for p in data], [self.blog_post.id, another_post.id]
        )

        results = self.client.execute(
            query, variables={"content_type": "bogus.ContentType"}
        )
        self.assertListEqual(results["data"]["pages"], [])

    def test_page(self):
        query = """
        query($id: Int) {
            page(id: $id) {
                contentType
                parent {
                    contentType
                }
            }
        }
        """

        executed = self.client.execute(query, variables={"id": self.blog_post.id})

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["page"]), dict_type)

        page_data = executed["data"]["page"]
        self.assertEquals(page_data["contentType"], "home.BlogPage")
        self.assertEquals(page_data["parent"]["contentType"], "home.HomePage")


class PageUrlPathTest(BaseGrappleTest):
    def _query_by_path(self, path, in_site=False):
        query = """
        query($urlPath: String, $inSite: Boolean) {
            page(urlPath: $urlPath, inSite: $inSite) {
                id
                url
            }
        }
        """

        executed = self.client.execute(
            query, variables={"urlPath": path, "inSite": in_site}
        )
        return executed["data"].get("page")

    def test_page_url_path_filter(self):
        home_child = BlogPageFactory(slug="child", parent=self.home)
        parent = BlogPageFactory(slug="parent", parent=self.home)

        child = BlogPageFactory(slug="child", parent=parent)

        page_data = self._query_by_path("/parent/child/")
        self.assertEquals(int(page_data["id"]), child.id)

        # query without trailing slash
        page_data = self._query_by_path("/parent/child")
        self.assertEquals(int(page_data["id"]), child.id)

        # we have two pages with the same slug, however /home/child will
        # be returned first because of its position in the tree
        page_data = self._query_by_path("/child")
        self.assertEquals(int(page_data["id"]), home_child.id)

        page_data = self._query_by_path("/")
        self.assertEquals(int(page_data["id"]), self.home.id)

        page_data = self._query_by_path("foo/bar")
        self.assertIsNone(page_data)

    def test_with_multisite(self):
        home_child = BlogPageFactory(slug="child", parent=self.home)

        another_home = HomePage.objects.create(
            title="Another home", slug="another-home", path="00010002", depth=2
        )
        another_site = wagtail_factories.SiteFactory(
            site_name="Another site", root_page=another_home
        )
        another_child = BlogPageFactory(slug="child", parent=another_home)

        # with multiple sites, only the first one will be returned
        page_data = self._query_by_path("/child/")
        self.assertEquals(int(page_data["id"]), home_child.id)

        with patch(
            f"{settings.WAGTAIL_CORE}.models.Site.find_for_request",
            return_value=another_site,
        ):
            page_data = self._query_by_path("/child/", in_site=True)
            self.assertEquals(int(page_data["id"]), another_child.id)

            page_data = self._query_by_path("/child", in_site=True)
            self.assertEquals(int(page_data["id"]), another_child.id)


class SitesTest(TestCase):
    def setUp(self):
        self.site = wagtail_factories.SiteFactory(
            hostname="grapple.localhost", site_name="Grapple test site"
        )
        self.client = Client(SCHEMA)
        self.home = HomePage.objects.first()

    def test_sites(self):
        query = """
        {
            sites {
                siteName
                hostname
                port
                isDefaultSite
                rootPage {
                    title
                }
                pages {
                    title
                }
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["sites"]), list)
        self.assertEquals(len(executed["data"]["sites"]), Site.objects.count())

    def test_site(self):
        query = """
        query($hostname: String) {
            site(hostname: $hostname) {
                siteName
                pages {
                    title
                }
            }
        }
        """

        executed = self.client.execute(
            query, variables={"hostname": self.site.hostname}
        )

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["site"]), dict_type)
        self.assertEquals(type(executed["data"]["site"]["pages"]), list)

        pages = Page.objects.in_site(self.site)

        self.assertEquals(len(executed["data"]["site"]["pages"]), pages.count())
        self.assertNotEqual(
            len(executed["data"]["site"]["pages"]), Page.objects.count()
        )

    def test_site_pages_content_type_filter(self):
        query = """
        query($hostname: String $content_type: String) {
            site(hostname: $hostname) {
                siteName
                pages(contentType: $content_type) {
                    title
                    contentType
                }
            }
        }
        """
        # grapple test site root page
        results = self.client.execute(
            query,
            variables={
                "hostname": self.site.hostname,
                "content_type": "wagtailcore.Page",
            },
        )
        data = results["data"]["site"]["pages"]
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]["title"], self.site.root_page.title)

        # Shouldn't return any data
        results = self.client.execute(
            query,
            variables={"hostname": self.site.hostname, "content_type": "home.HomePage"},
        )
        data = results["data"]["site"]["pages"]
        self.assertEquals(len(data), 0)

        # localhost root page
        results = self.client.execute(
            query,
            variables={
                "hostname": self.home.get_site().hostname,
                "content_type": "home.HomePage",
            },
        )
        data = results["data"]["site"]["pages"]
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]["contentType"], "home.HomePage")
        self.assertEquals(data[0]["title"], self.home.title)

        # Blog page under grapple test site
        blog = BlogPageFactory(
            parent=self.site.root_page, title="blog on grapple test site"
        )
        results = self.client.execute(
            query,
            variables={"hostname": self.site.hostname, "content_type": "home.BlogPage"},
        )
        data = results["data"]["site"]["pages"]
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]["contentType"], "home.BlogPage")
        self.assertEquals(data[0]["title"], blog.title)

        # Blog page under localhost
        blog = BlogPageFactory(parent=self.home, title="blog on localhost")
        results = self.client.execute(
            query,
            variables={
                "hostname": self.home.get_site().hostname,
                "content_type": "home.BlogPage",
            },
        )
        data = results["data"]["site"]["pages"]
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]["contentType"], "home.BlogPage")
        self.assertEquals(data[0]["title"], blog.title)


@override_settings(GRAPPLE={"AUTO_CAMELCASE": False})
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

        self.assertEquals(type(executed["data"]), dict_type)
        self.assertEquals(type(executed["data"]["pages"]), list)
        self.assertEquals(type(executed["data"]["pages"][0]), dict_type)
        self.assertEquals(type(executed["data"]["pages"][0]["title"]), str)
        self.assertEquals(type(executed["data"]["pages"][0]["url_path"]), str)

        # note: not using .all() as the pages query returns all pages with a depth > 1. Wagtail will normally have
        # only one page at depth 1 (RootPage). everything else lives under it.
        pages = Page.objects.filter(depth__gt=1)

        self.assertEquals(len(executed["data"]["pages"]), pages.count())


class ImagesTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.image_model = get_image_model()
        self.assertEqual(self.image_model.objects.all().count(), 0)
        self.example_image = wagtail_factories.ImageFactory(title="Example Image")
        self.example_image.full_clean()
        self.example_image.save()
        self.assertEqual(self.image_model.objects.all().count(), 1)

    def test_properties_on_saved_example_image(self):
        example_img = self.image_model.objects.first()

        self.assertEqual(example_img.id, 1)
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

        self.assertEquals(executed["data"]["images"][0]["id"], "1")
        self.assertEquals(
            executed["data"]["images"][0]["url"],
            "http://localhost:8000" + self.example_image.file.url,
        )
        self.assertEquals(
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

        self.assertEquals(executed["data"]["images"][0]["id"], "1")
        self.assertEquals(
            executed["data"]["images"][0]["rendition"]["url"],
            "http://localhost:8000"
            + self.example_image.get_rendition("width-200").file.url,
        )

    def test_renditions(self):
        query = """
        {
            image(id: 1) {
                rendition(width: 100) {
                    url
                }
            }
        }
        """

        executed = self.client.execute(query)
        self.assertIn("width-100", executed["data"]["image"]["rendition"]["url"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_renditions_with_allowed_image_filters_restrictions(self):
        def get_query(**kwargs):
            params = ",".join([f"{key}: {value}" for key, value in kwargs.items()])
            return (
                """
            {
                image(id: 1) {
                    rendition(%s) {
                        url
                    }
                }
            }
            """
                % params
            )

        executed = self.client.execute(get_query(width=100))
        self.assertIsNone(executed["data"]["image"]["rendition"])

        executed = self.client.execute(get_query(width=200))
        self.assertIsNotNone(executed["data"]["image"]["rendition"])
        self.assertIn("width-200", executed["data"]["image"]["rendition"]["url"])

    @override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]})
    def test_src_set(self):
        query = """
        {
            image(id: 1) {
                srcSet(sizes: [100, 200])
            }
        }
        """

        executed = self.client.execute(query)

        # only the width-200 rendition is allowed
        self.assertNotIn("width-100", executed["data"]["image"]["srcSet"])
        self.assertIn("width-200", executed["data"]["image"]["srcSet"])

    def test_rendition_allowed_method(self):
        self.assertTrue(rendition_allowed("width-100"))
        with override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": ["width-200"]}):
            self.assertFalse(rendition_allowed("width-100"))
            self.assertTrue(rendition_allowed("width-200"))

        with override_settings(GRAPPLE={"ALLOWED_IMAGE_FILTERS": []}):
            self.assertFalse(rendition_allowed("width-100"))
            self.assertFalse(rendition_allowed("fill-100x100"))

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
            title="Example File", file=uploaded_file
        )
        self.example_document.full_clean()
        self.example_document.save()
        self.example_document.get_file_hash()
        self.example_document.get_file_size()
        self.assertEqual(self.document_model.objects.all().count(), 1)

    def test_properties_on_saved_example_document(self):
        example_doc = self.document_model.objects.first()

        self.assertEqual(example_doc.id, 1)
        self.assertEqual(example_doc.title, "Example File")

        example_doc.file.seek(0)

        self.assertEqual(example_doc.file.readline(), b"Hello world!")

        self.assertNotEqual(example_doc.file_hash, "")
        self.assertNotEqual(example_doc.file_size, None)

    def test_query_documents_id(self):
        query = """
        {
            documents {
                id
                customDocumentProperty
            }
        }
        """

        executed = self.client.execute(query)

        documents = self.document_model.objects.all()

        self.assertEquals(len(executed["data"]["documents"]), documents.count())
        self.assertEquals(
            executed["data"]["documents"][0]["id"], str(self.example_document.id)
        )
        self.assertEquals(
            executed["data"]["documents"][0]["customDocumentProperty"],
            "Document Model!",
        )

    def test_query_file_field(self):
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
            executed["data"]["documents"][0]["file"], self.example_document.file.name
        )

    def test_query_file_hash_field(self):
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

    def test_query_file_size_field(self):
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

    def test_query_url_field_with_default_document_serve_method(self):
        query = """
        {
            documents {
                id
                url
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEqual(
            executed["data"]["documents"][0]["url"],
            "http://localhost:8000" + self.example_document.url,
        )

    def test_query_url_field_with_direct_document_serve_method(self):
        serve_method_at_test_start = settings.WAGTAILDOCS_SERVE_METHOD
        settings.WAGTAILDOCS_SERVE_METHOD = "direct"
        query = """
        {
            documents {
                id
                url
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEqual(
            executed["data"]["documents"][0]["url"],
            "http://localhost:8000" + self.example_document.file.url,
        )
        settings.WAGTAILDOCS_SERVE_METHOD = serve_method_at_test_start

    def tearDown(self):
        self.example_document.file.delete()


class MediaTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()

        self.media_model = get_media_model()
        self.assertEqual(self.media_model.objects.all().count(), 0)

        uploaded_file = SimpleUploadedFile("example.mp4", b"")
        self.media_item = self.media_model(
            title="Example Media File", file=uploaded_file, duration=0, type="video"
        )
        self.media_item.full_clean()
        self.media_item.save()
        self.assertEqual(self.media_model.objects.all().count(), 1)

    def test_properties_on_saved_example_media(self):
        media_item = self.media_model.objects.first()

        self.assertEqual(media_item.id, 1)
        self.assertEqual(media_item.title, "Example Media File")

    def test_query_media_id(self):
        query = """
        {
            media {
                id
            }
        }
        """

        executed = self.client.execute(query)

        media = self.media_model.objects.all()

        self.assertEquals(len(executed["data"]["media"]), media.count())
        self.assertEquals(executed["data"]["media"][0]["id"], str(self.media_item.id))

    def test_query_file_field(self):
        query = """
        {
            media {
                id
                file
            }
        }
        """

        executed = self.client.execute(query)

        self.assertEquals(
            executed["data"]["media"][0]["file"], self.media_item.file.name
        )

    def tearDown(self):
        self.media_item.file.delete()
