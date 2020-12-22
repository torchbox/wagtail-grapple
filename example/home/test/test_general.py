from example.tests.test_grapple import BaseGrappleTest

from home.factories import BlogPageFactory, SimpleModelFactory


class TestRegisterSingularQueryField(BaseGrappleTest):
    def test_singular_blog_page_query(self):
        def query():
            return """
        {
            firstPost {
                id
            }
        }
        """

        blog_post = BlogPageFactory()
        another_post = BlogPageFactory()
        results = self.client.execute(query())

        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), blog_post.id)

        results = self.client.execute(
            """
            {
                firstPost(order: "-id") {
                    id
                }
            }
            """
        )

        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), another_post.id)

    def test_singular_django_model_query(self):
        def query():
            return """
        {
            simpleModel {
                id
            }
        }
        """

        results = self.client.execute(query())
        self.assertTrue("simpleModel" in results["data"])
        self.assertIsNone(results["data"]["simpleModel"])

        instance = SimpleModelFactory()
        results = self.client.execute(query())

        self.assertEqual(int(results["data"]["simpleModel"]["id"]), instance.id)


class TestRegisterQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
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
        results = self.client.execute(query)
        data = results["data"]["posts"]
        self.assertEqual(len(data), 3)
        self.assertEqual(int(data[0]["id"]), self.child_post.id)
        self.assertEqual(int(data[1]["id"]), self.another_post.id)
        self.assertEqual(int(data[2]["id"]), self.blog_post.id)

    def test_query_field(self):
        def query(filters):
            return (
                """
            {
                post(%s) {
                    id
                    urlPath
                }
            }
            """
                % filters
            )

        # filter by id
        results = self.client.execute(query("id: %d" % self.blog_post.id))
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        # filter by url path
        results = self.client.execute(query('urlPath: "/post-one"'))
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        results = self.client.execute(query('urlPath: "/post-two/post-one"'))
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.child_post.id)

        # test query by slug.
        # Note: nothing should be returned if more than one page has the same slug
        results = self.client.execute(query('slug: "post-one"'))
        self.assertIsNone(results["data"]["post"])
        results = self.client.execute(query('slug: "post-two"'))
        data = results["data"]["post"]
        self.assertEqual(int(data["id"]), self.another_post.id)


class TestRegisterPaginatedQueryField(BaseGrappleTest):
    def setUp(self):
        super().setUp()
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
        results = self.client.execute(query)
        data = results["data"]["blogPages"]
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(int(data["items"][0]["id"]), self.child_post.id)
        self.assertEqual(int(data["pagination"]["totalPages"]), 3)

    def test_query_field(self):
        def query(filters):
            return (
                """
            {
                blogPage(%s) {
                    id
                    urlPath
                }
            }
            """
                % filters
            )

        # filter by id
        results = self.client.execute(query("id: %d" % self.blog_post.id))
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        # filter by url path
        results = self.client.execute(query('urlPath: "/post-one"'))
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.blog_post.id)

        results = self.client.execute(query('urlPath: "/post-two/post-one"'))
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.child_post.id)

        # test query by slug.
        # Note: nothing should be returned if more than one page has the same slug
        results = self.client.execute(query('slug: "post-one"'))
        self.assertIsNone(results["data"]["blogPage"])
        results = self.client.execute(query('slug: "post-two"'))
        data = results["data"]["blogPage"]
        self.assertEqual(int(data["id"]), self.another_post.id)
