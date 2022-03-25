from example.tests.test_grapple import BaseGrappleTest
from grapple.settings import has_channels

if has_channels:

    class TestRegisterSubscription(BaseGrappleTest):
        def test_subscription(self):
            query = """
            {
              __schema {
                subscriptionType {
                  fields {
                    name
                  }
                }
              }
            }
            """

            results = self.client.execute(query)
            subscriptions = results["data"]["__schema"]["subscriptionType"]["fields"]

            # We check here that the subscription defined in example/home/subscriptions.py and
            # added in example/home/wagtail_hooks.py is indeed added to the graphene schema.
            # Note: it is hard to test subscriptions, but there is some place for improvement here.
            self.assertIn("hello", [item["name"] for item in subscriptions])
