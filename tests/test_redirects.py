from test_grapple import BaseGrappleTest
from testapp.factories import RedirectFactory
from testapp.models import BlogPage
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site
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

        # Create a basic redirect without a specified `redirect_page` or `site`.
        RedirectFactory(
            old_path="/test/old",
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

        # Verify that the structure of the results is correct.
        self.assertEqual(type(result["data"]), dict)
        self.assertEqual(type(result["data"]["redirects"]), list)
        self.assertEqual(type(result["data"]["redirects"][0]), dict)

        result_data = result["data"]["redirects"][0]

        self.assertEqual(result_data["oldPath"], "/test/old")
        self.assertEqual(result_data["newUrl"], "http://localhost:8000/test/new")
        self.assertEqual(result_data["isPermanent"], True)

    def test_sub_type_query(self):
        """
        Test that `Page` and `Site` fields on Redirects can be queried through graphql.
        """

        # Create a redirect with specified `redirect_page` and `site`.
        RedirectFactory(
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

        # Verify the structure of the query for `page` and `site`.
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

        # Create a redirect with both `redirect_link` and `redirect_page`.
        RedirectFactory(redirect_link="/test/incorrect", redirect_page=self.page)
        # Create a redirect with just `redirect_page`.
        RedirectFactory(
            redirect_link="",
            is_permanent=True,
            redirect_page=self.page,
        )
        # Create a redirect with just `redirect_link`.
        RedirectFactory(redirect_link="http://test/just-link", redirect_page=None)

        query = """
        {
            redirects {
                newUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"]

        # Sanity check to ensure only those three redirect objects are in the database.
        self.assertEqual(Redirect.objects.count(), 3)

        # Redirects with a specified `redirect_page` should return its url.
        self.assertEqual(result[0]["newUrl"], "http://localhost/test-page-url/")
        self.assertEqual(result[1]["newUrl"], "http://localhost/test-page-url/")
        # Redirects without a specified `redirect_page` should return the
        # `redirect_link` instead.
        self.assertEqual(result[2]["newUrl"], "http://test/just-link")

    def test_no_new_url_query(self):
        """
        Test that a redirect can be created without a `redirect_link` or
        `redirect_page` and queried. This can be used for producing a HTTP 410
        for any pages/URLs that are no longer in existence.
        """

        # Create a redirect with no source for `new_url` generation.
        RedirectFactory(
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
        # Create a redirect with `site` using port 81, which should result in a
        # standard `old_url` generation.
        RedirectFactory(
            old_path="old-path",
            site=SiteFactory(
                hostname="test-site",
                port=81,
            ),
        )
        # Create a redirect with `site` using port 80, which should be resolved
        # to "http" without a specified port in `old_url`.
        RedirectFactory(
            old_path="old-path",
            site=SiteFactory(
                hostname="test-site-default-port",
                port=80,
            ),
        )
        # Create a redirect with `site` using port 443, which should be resolved
        # to "https" without a specified port in `old_url`.
        RedirectFactory(
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

        # Sanity check to ensure only those three redirect objects are in the database.
        self.assertEqual(Redirect.objects.count(), 3)

        self.assertEqual(result[0]["oldUrl"], "http://test-site:81/old-path")
        self.assertEqual(result[1]["oldUrl"], "http://test-site-default-port/old-path")
        self.assertEqual(result[2]["oldUrl"], "https://test-site-secure/old-path")

    def test_all_sites_url(self):
        """
        Test that when no site is specified on a redirect, that redirect is
        shown for each existing site.
        """

        # Create two additional sites (on top of the default `Localhost` one).
        SiteFactory(hostname="test-site", port=81)
        SiteFactory(hostname="another-test-site", port=82)

        # Create a `Redirect` without a `site` (treated as active for all sites).
        RedirectFactory(
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

        result = self.client.execute(query)["data"]["redirects"]

        # Sanity check to ensure there are three `Site`s.
        self.assertEqual(Site.objects.count(), 3)

        # Sanity check to ensure only one `Redirect` is in the database.
        self.assertEqual(Redirect.objects.count(), 1)

        # Ensure there are three `Redirect`s returned despite only 1 object
        # in the database.
        self.assertEqual(len(result), 3)

        self.assertEqual(result[0]["oldUrl"], "http://another-test-site:82/old-path")
        self.assertEqual(result[1]["oldUrl"], "http://localhost/old-path")
        self.assertEqual(result[2]["oldUrl"], "http://test-site:81/old-path")

    def test_query_efficiency(self):
        """
        Verify the number of queries when querying Redirects is constant to
        prevent n+1 queries.
        """

        # Number of queries should remain constant for any N of redirects.
        RedirectFactory()
        RedirectFactory()
        RedirectFactory()

        query = """
        {
            redirects {
                oldPath
                newUrl
                isPermanent
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

        # There should be one SELECT query for Redirects and one for Sites.
        with self.assertNumQueries(2):
            self.client.execute(query)

    def test_new_url_is_absolute(self):
        """Test that the `new url` is always an absolute url."""

        # Create a redirect with just `redirect_page`.
        RedirectFactory(
            redirect_link="",
            redirect_page=self.page,
        )
        # Create a redirect with absolute url in `redirect_link`.
        RedirectFactory(
            redirect_link="http://test.com/",
            redirect_page=None,
        )

        # Create a redirect with relative url in `redirect_link`.
        RedirectFactory(
            redirect_link="/test",
            redirect_page=None,
            site=SiteFactory(
                hostname="test-site",
                port=81,
            ),
        )

        query = """
        {
            redirects {
                newUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"]

        # assert all urls are absolute
        self.assertEqual(result[0]["newUrl"], "http://localhost/test-page-url/")
        self.assertEqual(result[1]["newUrl"], "http://test.com/")
        self.assertEqual(result[2]["newUrl"], "http://test-site:81/test")
