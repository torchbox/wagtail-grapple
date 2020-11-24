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

    def test_advert_all_query_required(self):
        queries = self.client.schema.introspect()["__schema"]["types"][0]["fields"]
        adverts_query = list(filter(lambda x: x["name"] == "adverts", queries))[0]
        adverts_query_kind = adverts_query["type"]["kind"]
        adverts_query_type = adverts_query["type"]["ofType"]

        self.assertTrue(adverts_query_kind == "NON_NULL")
        self.assertTrue(adverts_query_type["kind"] == "LIST")
        self.assertTrue(adverts_query_type["ofType"]["kind"] == "NON_NULL")
        self.assertTrue(adverts_query_type["ofType"]["ofType"]["kind"] == "OBJECT")
        self.assertTrue(adverts_query_type["ofType"]["ofType"]["name"] == "Advert")

    def test_advert_single_query_required(self):
        queries = self.client.schema.introspect()["__schema"]["types"][0]["fields"]
        advert_query = list(filter(lambda x: x["name"] == "advert", queries))[0]
        advert_query_kind = advert_query["type"]["kind"]
        advert_query_type = advert_query["type"]["ofType"]

        self.assertTrue(advert_query_kind == "NON_NULL")
        self.assertTrue(advert_query_type["kind"] == "OBJECT")
        self.assertTrue(advert_query_type["name"] == "Advert")
