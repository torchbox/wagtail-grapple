import json

from test_grapple import BaseGrappleTest
from testapp.factories import RedirectFactory
from testapp.models import BlogPage
from wagtail_factories import SiteFactory


class TestRedirectQueries(BaseGrappleTest):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.page = BlogPage(title="Test page", slug="test-page-url", date="2020-01-01")
        cls.home.add_child(instance=cls.page)

    def test_basic_query(self):
        """
        Test that Redirect fields can be queried through graphql.
        """

        self.redirect = RedirectFactory(
            old_path="test/old",
            redirect_link="http://localhost:8000/test/new",
            is_permanent=True,
            redirect_page=None,
            site=None,
        )

        query = """
        {
            redirects {
                oldPath
                newUrl
                isPermanent
            }
        }
        """

        result = self.client.execute(query)

        self.assertEqual(type(result["data"]), dict)
        self.assertEqual(type(result["data"]["redirects"]), list)
        self.assertEqual(type(result["data"]["redirects"][0]), dict)

        result_data = result["data"]["redirects"][0]

        self.assertEqual(result_data["oldPath"], "test/old")
        self.assertEqual(result_data["newUrl"], "http://localhost:8000/test/new")
        self.assertEqual(result_data["isPermanent"], True)

    def test_sub_type_query(self):
        """
        Test that `Page` and `Site` fields on Redirects can be queried through graphql.
        """

        self.redirect = RedirectFactory(
            redirect_page=self.page,
            site=SiteFactory(
                hostname="test-site",
                port=81,
            ),
        )

        query = """
        {
            redirects {
                page {
                    title
                    url
                }
                site {
                    hostname
                    port
                }
            }
        }
        """

        result = self.client.execute(query)

        self.assertEqual(type(result["data"]["redirects"][0]), dict)
        self.assertEqual(type(result["data"]["redirects"][0]["page"]), dict)
        self.assertEqual(type(result["data"]["redirects"][0]["site"]), dict)

        result_data = result["data"]["redirects"][0]

        self.assertEqual(result_data["page"]["title"], "Test page")
        self.assertEqual(result_data["page"]["url"], "http://localhost/test-page-url/")
        self.assertEqual(result_data["site"]["hostname"], "test-site")
        self.assertEqual(result_data["site"]["port"], 81)

    def test_new_url_sources(self):
        """
        Test that when redirects are queried, the right source for `newUrl` is chosen.
        When both are provided: `newUrl` is taken from `redirect page` rather than `redirect link`.
        When just one is provided, use that.
        """

        self.redirect_both_sources = RedirectFactory(
            redirect_link="/test/incorrect", redirect_page=self.page
        )
        self.redirect_just_page = RedirectFactory(
            redirect_link="",
            is_permanent=True,
            redirect_page=self.page,
        )
        self.redirect_just_link = RedirectFactory(
            redirect_link="http://test/just-link", redirect_page=None
        )

        query = """
        {
            redirects {
                newUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"]

        self.assertEqual(result[0]["newUrl"], "http://localhost/test-page-url/")
        self.assertEqual(result[1]["newUrl"], "http://localhost/test-page-url/")
        self.assertEqual(result[2]["newUrl"], "http://test/just-link")

    def test_no_new_url_query(self):
        """
        Test that a redirect can be created without a `redirect_link` or
        `redirect_page` and queried. This can be used for producing a HTTP 410
        for any pages/URLs that are no longer in existence.
        """
        self.redirect = RedirectFactory(
            redirect_link="",
            redirect_page=None,
        )

        query = """
        {
            redirects {
                newUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"][0]["newUrl"]

        self.assertEqual(result, None)

    def test_specified_site_url(self):
        """
        Test that a redirect with a specified site returns the correct `old_url`.
        """
        self.redirect = RedirectFactory(
            old_path="old-path",
            site=SiteFactory(
                hostname="test-site",
                port=81,
            ),
        )
        self.redirect = RedirectFactory(
            old_path="old-path",
            site=SiteFactory(
                hostname="test-site-default-port",
                port=80,
            ),
        )
        self.redirect = RedirectFactory(
            old_path="old-path",
            site=SiteFactory(
                hostname="test-site-secure",
                port=443,
            ),
        )

        query = """
        {
            redirects {
                oldUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"]

        self.assertEqual(result[0]["oldUrl"], "http://test-site:81/old-path")
        self.assertEqual(result[1]["oldUrl"], "http://test-site-default-port/old-path")
        self.assertEqual(result[2]["oldUrl"], "https://test-site-secure/old-path")

    def test_all_sites_url(self):
        """
        Test that a redirect with no specified site return the desired result
        for "all sites".
        """
        self.site1 = SiteFactory(hostname="test-site", port=8000)
        self.site2 = SiteFactory(hostname="another-test-site", port=8001)

        self.redirect = RedirectFactory(
            old_path="old-path",
            site=None,
        )

        query = """
        {
            redirects {
                oldUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"][0]["oldUrl"]
        result = json.loads(result)

        self.assertIn("http://localhost:80/old-path", result)
        self.assertIn("http://test-site:8000/old-path", result)
        self.assertIn("http://another-test-site:8001/old-path", result)
