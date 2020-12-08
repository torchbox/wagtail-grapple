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
