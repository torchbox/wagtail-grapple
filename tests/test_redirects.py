from test_grapple import BaseGrappleTest
from testapp.factories import RedirectFactory
from testapp.models import BlogPage


class TestRedirectQueries(BaseGrappleTest):
    def setUp(self) -> None:
        super().setUp()
        self.page = BlogPage(title="Test page", slug="test-page-url", date="2020-01-01")
        self.home.add_child(instance=self.page)

    def test_basic_query(self):
        """
        Test that Redirect fields can be queried through graphql.
        """

        self.redirect = RedirectFactory(
            old_path="/test/old",
            redirect_link="http://localhost:8000/test/new",
            is_permanent=True,
            redirect_page=None,
        )

        query = """
        {
            redirects {
                oldPath
                oldUrl
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

        self.assertEqual(result_data["oldPath"], "/test/old")
        self.assertEqual(result_data["oldUrl"], "http://localhost:8000/test/old")
        self.assertEqual(result_data["newUrl"], "http://localhost:8000/test/new")
        self.assertEqual(result_data["isPermanent"], True)

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
            redirect_link="/test/just-link", redirect_page=None
        )

        query = """
        {
            redirects {
                newUrl
            }
        }
        """

        result = self.client.execute(query)["data"]["redirects"]

        self.assertEqual(result[0]["newUrl"], "/test-page-url/")
        self.assertEqual(result[1]["newUrl"], "/test-page-url/")
        self.assertEqual(result[2]["newUrl"], "/test/just-link")

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
