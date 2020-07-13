from example.tests.test_grapple import BaseGrappleTest
from home.factories import AdvertFactory


class AdvertTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        # Create advert
        self.advert = AdvertFactory()

    def validate_advert(self, advert):
        # Check all the fields
        self.assertTrue(isinstance(advert["id"], str))
        self.assertTrue(isinstance(advert["url"], str))
        self.assertTrue(isinstance(advert["text"], str))

    def test_advert_all_query(self):
        query = """
        {
           adverts {
                id
                url
                text
            }
        }
        """
        executed = self.client.execute(query)
        advert = executed["data"]["adverts"][0]

        # Check all the fields
        self.validate_advert(advert)

    def test_advert_single_query(self):
        query = """
        {
           advert(url:"%s") {
                id
                url
                text
            }
        }
        """ % (
            self.advert.url
        )
        executed = self.client.execute(query)
        advert = executed["data"]["advert"]

        # Check all the fields
        self.validate_advert(advert)
