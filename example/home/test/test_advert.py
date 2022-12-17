from django.test import override_settings
from home.factories import AdvertFactory

from example.tests.test_grapple import BaseGrappleTestWithIntrospection


class AdvertTest(BaseGrappleTestWithIntrospection):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.richtext_sample = (
            f'Text with a \'link\' to <a linktype="page" id="{cls.home.id}">Home</a>'
        )
        cls.richtext_sample_rendered = (
            f"Text with a 'link' to <a href=\"{cls.home.url}\">Home</a>"
        )
        cls.advert = AdvertFactory(
            rich_text=cls.richtext_sample, extra_rich_text=cls.richtext_sample
        )

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
        query($url: String) {
           advert(url: $url) {
                id
                url
                text
            }
        }
        """
        executed = self.client.execute(query, variables={"url": self.advert.url})
        advert = executed["data"]["advert"]

        # Check all the fields
        self.validate_advert(advert)

    def test_advert_all_query_required(self):
        adverts_query = list(
            filter(lambda x: x["name"] == "adverts", self.available_queries)
        )[0]
        adverts_query_kind = adverts_query["type"]["kind"]
        adverts_query_type = adverts_query["type"]["ofType"]

        self.assertTrue(adverts_query_kind == "NON_NULL")
        self.assertTrue(adverts_query_type["kind"] == "LIST")
        self.assertTrue(adverts_query_type["ofType"]["kind"] == "NON_NULL")
        self.assertTrue(adverts_query_type["ofType"]["ofType"]["kind"] == "OBJECT")
        self.assertTrue(adverts_query_type["ofType"]["ofType"]["name"] == "Advert")

    def test_advert_single_query_required(self):
        advert_query = list(
            filter(lambda x: x["name"] == "advert", self.available_queries)
        )[0]
        advert_query_kind = advert_query["type"]["kind"]
        advert_query_type = advert_query["type"]["ofType"]

        self.assertTrue(advert_query_kind == "NON_NULL")
        self.assertTrue(advert_query_type["kind"] == "OBJECT")
        self.assertTrue(advert_query_type["name"] == "Advert")

    def test_advert_single_query_rich_text(self):
        query = """
        query($url: String) {
           advert(url: $url) {
                richText
                stringRichText
                extraRichText
            }
        }
        """
        executed = self.client.execute(query, variables={"url": self.advert.url})
        advert = executed["data"]["advert"]

        # Field declared with GraphQLRichText
        self.assertEqual(advert["richText"], self.richtext_sample_rendered)

        # Declared with GraphQLString, custom field source
        self.assertEqual(advert["stringRichText"], self.richtext_sample_rendered)

        # Declared with GraphQLString, default field source
        self.assertEqual(advert["extraRichText"], self.richtext_sample_rendered)

        with override_settings(GRAPPLE={"RICHTEXT_FORMAT": "raw"}):
            executed = self.client.execute(query, variables={"url": self.advert.url})
            advert = executed["data"]["advert"]
            self.assertEqual(advert["richText"], self.richtext_sample)
            self.assertEqual(advert["stringRichText"], self.richtext_sample)
            self.assertEqual(advert["extraRichText"], self.richtext_sample)
