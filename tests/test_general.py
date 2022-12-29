import uuid

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, override_settings
from test_grapple import BaseGrappleTest
from testapp.factories import (
    AdvertFactory,
    BlogPageFactory,
    MiddlewareModelFactory,
    SimpleModelFactory,
)


class AuthenticatedUser(AnonymousUser):
    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True


class TestRegisterSingularQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = AnonymousUser()

    def test_singular_blog_page_query(self):
        query = """
        {
            firstPost {
                id
            }
        }
        """

        blog_post = BlogPageFactory()
        another_post = BlogPageFactory()
        results = self.client.execute(query, context_value=self.request)

        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), blog_post.id)

        query = """
        {
            firstPost(order: "-id") {
                id
            }
        }
        """
        results = self.client.execute(query, context_value=self.request)

        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), another_post.id)

    def test_singular_django_model_query(self):
        query = """
        {
            simpleModel {
                id
            }
        }
        """

        results = self.client.execute(query)
        self.assertTrue("simpleModel" in results["data"])
        self.assertIsNone(results["data"]["simpleModel"])

        instance = SimpleModelFactory()
        results = self.client.execute(query)

        self.assertEqual(int(results["data"]["simpleModel"]["id"]), instance.id)


class TestRegisterQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = AnonymousUser()
        self.blog_post = BlogPageFactory(parent=self.home, slug="post-one")
        self.another_post = BlogPageFactory(parent=self.home, slug="post-two")
        self.child_post = BlogPageFactory(parent=self.another_post, slug="post-one")
        self.middleware_instance = MiddlewareModelFactory()

    def test_query_field_plural(self):
        query = """
        {
            posts {
                id
            }
        }
        """
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["posts"]
        self.assertEqual(len(data), 3)
        ids = [int(d["id"]) for d in data]
        self.assertIn(self.blog_post.id, ids)
        self.assertIn(self.another_post.id, ids)
        self.assertIn(self.child_post.id, ids)

    def test_query_field(self):
        query = """
        query ($id: Int, $urlPath: String, $slug: String) {
            post(id: $id, urlPath: $urlPath, slug: $slug) {
                id
                urlPath
            }
        }
        """

        # filter by id
        results = self.client.execute(
            query, variables={"id": self.blog_post.id}, context_value=self.request
        )
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        # filter by url path
        results = self.client.execute(
            query, variables={"urlPath": "/post-one"}, context_value=self.request
        )
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        results = self.client.execute(
            query,
            variables={"urlPath": "/post-two/post-one"},
            context_value=self.request,
        )
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.child_post.id)

        # test query by slug.
        # Note: nothing should be returned if more than one page has the same slug
        results = self.client.execute(
            query, variables={"slug": "post-one"}, context_value=self.request
        )
        self.assertIsNone(results["data"]["post"])
        results = self.client.execute(
            query, variables={"slug": "post-two"}, context_value=self.request
        )
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.another_post.id)

    def test_multiple_middleware(self):
        query = """
        query ($id: Int) {
            middlewareModel(id: $id) {
                id
            }
        }
        """
        results = self.client.execute(
            query, variables={"id": 1}, context_value=self.request
        )
        # Check that both middleware ran ok, value returned means the check for middleware_1 passed in middleware_2
        self.assertEqual(int(results["data"]["middlewareModel"]["id"]), 1)
        results = self.client.execute(
            query, variables={"id": 2}, context_value=self.request
        )
        # Check that the second middleware failed when id = 2
        self.assertEqual(results["data"]["middlewareModel"], None)


class TestRegisterPaginatedQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = AnonymousUser()
        self.blog_post = BlogPageFactory(parent=self.home, slug="post-one")
        self.another_post = BlogPageFactory(parent=self.home, slug="post-two")
        self.child_post = BlogPageFactory(parent=self.another_post, slug="post-one")

    def test_paginated_query_field(self):
        query = """
        query ($id: Int, $urlPath: String, $slug: String) {
            blogPage(id: $id, urlPath: $urlPath, slug: $slug) {
                id
                urlPath
            }
        }
        """

        # filter by id
        results = self.client.execute(
            query, variables={"id": self.blog_post.id}, context_value=self.request
        )
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        # filter by url path
        results = self.client.execute(
            query, variables={"urlPath": "/post-one"}, context_value=self.request
        )
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        results = self.client.execute(
            query,
            variables={"urlPath": "/post-two/post-one"},
            context_value=self.request,
        )
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.child_post.id)

        # test query by slug.
        # Note: nothing should be returned if more than one page has the same slug
        results = self.client.execute(
            query, variables={"slug": "post-one"}, context_value=self.request
        )
        self.assertIsNone(results["data"]["blogPage"])
        results = self.client.execute(
            query, variables={"slug": "post-two"}, context_value=self.request
        )
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.another_post.id)

    def test_paginated_query_field_plural(self):
        query = """
        {
            blogPages(perPage: 1, order: "title") {
                items {
                    id
                }
                pagination {
                    totalPages
                }
            }
        }
        """
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["blogPages"]
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(int(data["pagination"]["totalPages"]), 3)

    @override_settings(GRAPPLE={"PAGE_SIZE": 2})
    def test_paginated_query_field_plural_default_per_page(self):
        query = """
        {
            blogPages {
                items {
                    id
                }
                pagination {
                    perPage
                    totalPages
                }
            }
        }
        """
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["blogPages"]
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(int(data["pagination"]["perPage"]), 2)
        self.assertEqual(int(data["pagination"]["totalPages"]), 2)

    @override_settings(GRAPPLE={"MAX_PAGE_SIZE": 3})
    def test_paginated_query_field_plural_default_max_per_page(self):
        query = """
        {
            blogPages(perPage: 5) {
                items {
                    id
                }
                pagination {
                    perPage
                    totalPages
                }
            }
        }
        """
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["blogPages"]
        self.assertEqual(len(data["items"]), 3)
        self.assertEqual(int(data["pagination"]["perPage"]), 3)
        self.assertEqual(int(data["pagination"]["totalPages"]), 1)


class TestRegisterMutation(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.blog_post = BlogPageFactory(parent=self.home, slug="post-one")
        self.name = "Jean-Claude"
        # A randomly generated slug is set here in order to avoid conflicted slug during tests
        self.slug = str(uuid.uuid4().hex[:6].upper())

    def test_mutation(self):
        query = """
        mutation($name: String, $parent: Int, $slug: String) {
          createAuthor(name: $name, parent: $parent, slug: $slug) {
            author {
              id
              ...on AuthorPage {
                  name
              }
              title
              slug
            }
          }
        }
        """

        results = self.client.execute(
            query,
            variables={
                "name": self.name,
                "parent": self.blog_post.id,
                "slug": self.slug,
            },
        )
        data = results["data"]["createAuthor"]
        self.assertIn("author", data)

        # First we check that standard page fields are available in the returned query
        self.assertIn("id", data["author"])
        self.assertIn("title", data["author"])
        self.assertIn("slug", data["author"])

        # Now we ensure that AuthorPage-specific fields are well returned
        self.assertIn("name", data["author"])

        # Finally, we ensure that data passed in the first place to the query are indeed
        # returned after the author has been saved to the database.
        self.assertEqual(data["author"]["name"], self.name)
        self.assertEqual(data["author"]["slug"], self.slug)


class TestUtils(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        BlogPageFactory(parent=self.home, title="Test post 1", slug="post-one")
        BlogPageFactory(parent=self.home, title="Test post 2", slug="post-two")
        BlogPageFactory(parent=self.home, title="Test post 3", slug="post-three")

    def _query_pages(self, limit=None, offset=None):
        query = """
        query ($limit: PositiveInt, $offset: PositiveInt) {
            pages(contentType: "testapp.BlogPage", order: "title", limit: $limit, offset: $offset) {
                title
            }
        }
        """
        results = self.client.execute(
            query,
            variables={"limit": limit, "offset": offset},
        )
        return results["data"]["pages"]

    def test_page_size_is_default_limit(self):
        with override_settings(GRAPPLE={"PAGE_SIZE": 3, "MAX_PAGE_SIZE": 8}):
            pages = self._query_pages()
        self.assertEqual(len(pages), 3)

    def test_limit_supercedes_page_size(self):
        with override_settings(GRAPPLE={"PAGE_SIZE": 3, "MAX_PAGE_SIZE": 8}):
            pages = self._query_pages(5)
        self.assertEqual(len(pages), 3)

    def test_max_page_size_supercedes_page_size(self):
        # the max page size is 1 and we should get only one,
        # even if default page size and the requested limit are higher
        with override_settings(GRAPPLE={"PAGE_SIZE": 10, "MAX_PAGE_SIZE": 1}):
            pages = self._query_pages(None)

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["title"], "Test post 1")

    def test_max_page_size_supercedes_limit(self):
        # Default page size is one, but we ask for two which is still less than max page size
        with override_settings(GRAPPLE={"PAGE_SIZE": 1, "MAX_PAGE_SIZE": 2}):
            pages = self._query_pages(5)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["title"], "Test post 1")

    def test_offset(self):
        pages = self._query_pages(1)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["title"], "Test post 1")

        pages = self._query_pages(2, 1)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["title"], "Test post 2")
        self.assertEqual(pages[1]["title"], "Test post 3")


class TestRichTextType(BaseGrappleTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.richtext_sample = (
            f'Text with a \'link\' to <a linktype="page" id="{cls.home.id}">Home</a>'
        )
        cls.richtext_sample_rendered = (
            f"Text with a 'link' to <a href=\"{cls.home.url}\">Home</a>"
        )

    def test_mutate_rich_text_type(self):
        query = """
        mutation($url: String!, $text: String!, $richText: RichText) {
            createAdvert(url: $url, text: $text, richText: $richText) {
                advert {
                    id
                    url
                    text
                    richText
                }
            }
        }
        """
        result = self.client.execute(
            query,
            variables={
                "url": "https://http.cat",
                "text": "cats",
                "richText": self.richtext_sample,
            },
        )
        self.assertEqual(
            result["data"]["createAdvert"]["advert"]["richText"],
            self.richtext_sample_rendered,
        )

        query = """
        mutation($id: ID!, $url: String, $text: String, $richText: RichText) {
            updateAdvert(id: $id, url: $url, text: $text, richText: $richText) {
                advert {
                    id
                    url
                    text
                    richText
                }
            }
        }
        """
        advert_id = result["data"]["createAdvert"]["advert"]["id"]
        rich_text = "<b>dogs</b>"
        result = self.client.execute(
            query, variables={"id": advert_id, "richText": rich_text}
        )
        self.assertEqual(
            result["data"]["updateAdvert"]["advert"]["richText"], rich_text
        )


class TestFieldMiddleware(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.blog_post = BlogPageFactory(parent=self.home, slug="post-one")

        self.request = RequestFactory()
        self.request.user = AnonymousUser()

    def test_singular_query_field_with_logged_in_user_should_return_nothing(self):
        query = """
        {
            firstPost {
                id
            }
        }
        """
        self.request.user = AuthenticatedUser()
        results = self.client.execute(query, context_value=self.request)

        data = results["data"]["firstPost"]
        self.assertEqual(data, None)

    def test_query_field_with_logged_in_user_should_return_nothing(self):
        """
        The query field was registered with the anonymous middleware, i.e. requires only anonymous users
        """

        query = """
        query ($id: Int) {
            post(id: $id) {
                id
                urlPath
            }
        }
        """

        self.request.user = AuthenticatedUser()
        # filter by id
        results = self.client.execute(
            query, variables={"id": self.blog_post.id}, context_value=self.request
        )
        data = results["data"]["post"]
        self.assertEqual(data, None)

    def test_query_field_plural_with_logged_in_user_should_return_nothing(self):
        """
        The query field was registered with the anonymous middleware, i.e. requires only anonymous users
        """

        query = """
        {
            posts {
                id
            }
        }
        """
        self.request.user = AuthenticatedUser()
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["posts"]
        self.assertEqual(data, None)

    def test_paginated_query_field_with_logged_in_user_should_return_nothing(self):
        """
        The query field was registered with the anonymous middleware, i.e. requires only anonymous users
        """
        query = """
        query ($id: Int) {
            blogPage(id: $id) {
                id
                urlPath
            }
        }
        """

        self.request.user = AuthenticatedUser()
        # filter by id
        results = self.client.execute(
            query, variables={"id": self.blog_post.id}, context_value=self.request
        )
        data = results["data"]["blogPage"]
        self.assertEqual(data, None)

    def test_paginated_query_field_plural_with_authenticated_user_should_return_nothing(
        self,
    ):
        """
        The query field was registered with the anonymous middleware, i.e. requires only anonymous users
        """

        query = """
        {
            blogPages(perPage: 1) {
                items {
                    id
                }
                pagination {
                    totalPages
                }
            }
        }
        """
        self.request.user = AuthenticatedUser()
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["blogPages"]
        self.assertEqual(data, None)

    def test_function_middleware(self):
        advert = AdvertFactory(text="test")

        query = """
        query($url: String) {
           advert(url: $url) {
                text
            }
        }
        """
        self.client.execute(
            query, variables={"url": advert.url}, context_value=self.request
        )
        self.assertTrue(self.request.custom_middleware)
