import uuid

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, override_settings
from home.factories import BlogPageFactory, SimpleModelFactory

from example.tests.test_grapple import BaseGrappleTest


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

    def test_singular_blog_page_query_with_user(self):
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
        self.assertEqual(int(data[0]["id"]), self.child_post.id)
        self.assertEqual(int(data[1]["id"]), self.another_post.id)
        self.assertEqual(int(data[2]["id"]), self.blog_post.id)

    def test_query_field_plural_with_user(self):
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

    def test_query_field_with_user(self):
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


class TestRegisterPaginatedQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = AnonymousUser()
        self.blog_post = BlogPageFactory(parent=self.home, slug="post-one")
        self.another_post = BlogPageFactory(parent=self.home, slug="post-two")
        self.child_post = BlogPageFactory(parent=self.another_post, slug="post-one")

    def test_query_field_plural(self):
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
        results = self.client.execute(query, context_value=self.request)
        data = results["data"]["blogPages"]
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(int(data["items"][0]["id"]), self.child_post.id)
        self.assertEqual(int(data["pagination"]["totalPages"]), 3)

    def test_query_field_plural_with_user(self):
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

    @override_settings(GRAPPLE={"PAGE_SIZE": 2})
    def test_query_field_plural_default_per_page(self):
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
        self.assertEqual(int(data["items"][0]["id"]), self.child_post.id)
        self.assertEqual(int(data["pagination"]["perPage"]), 2)
        self.assertEqual(int(data["pagination"]["totalPages"]), 2)

    @override_settings(GRAPPLE={"MAX_PAGE_SIZE": 3})
    def test_query_field_plural_default_max_per_page(self):
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
        self.assertEqual(int(data["items"][0]["id"]), self.child_post.id)
        self.assertEqual(int(data["pagination"]["perPage"]), 3)
        self.assertEqual(int(data["pagination"]["totalPages"]), 1)

    def test_query_field(self):
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

    def test_query_field_with_user(self):
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

    def test_pages_search(self):
        query = """
        query ($term: String, $limit: PositiveInt, $offset: PositiveInt) {
            pages(searchQuery: $term, limit: $limit, offset: $offset) {
                title
            }
        }
        """

        results = self.client.execute(
            query,
            variables={"term": "Test", "limit": 1},
        )
        pages = results["data"]["pages"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["title"], "Test post 1")

        results = self.client.execute(
            query,
            variables={"term": "Test", "limit": 2, "offset": 1},
        )
        pages = results["data"]["pages"]
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["title"], "Test post 2")
        self.assertEqual(pages[1]["title"], "Test post 3")

    def test_pages_search_with_min_max_page_size_settings(self):
        query = """
        query ($term: String, $limit: PositiveInt, $offset: PositiveInt) {
            pages(searchQuery: $term, limit: $limit, offset: $offset) {
                title
            }
        }
        """

        # the max page size is 1 and we should get only one,
        # even if default page size and the requested limit are higher
        with override_settings(GRAPPLE={"PAGE_SIZE": 10, "MAX_PAGE_SIZE": 1}):
            results = self.client.execute(
                query,
                variables={"term": "Test", "limit": 2},
            )

        pages = results["data"]["pages"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["title"], "Test post 1")

        # Default page size is one, but we ask for two which is still less than max page size
        with override_settings(GRAPPLE={"PAGE_SIZE": 1, "MAX_PAGE_SIZE": 5}):
            results = self.client.execute(
                query,
                variables={"term": "Test", "limit": 2},
            )

        pages = results["data"]["pages"]
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["title"], "Test post 1")
        self.assertEqual(pages[1]["title"], "Test post 2")


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
