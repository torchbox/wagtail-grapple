import wagtail_factories
from django.test import TestCase
from graphql import GraphQLError

from grapple.utils import resolve_site


class TestResolveSite(TestCase):
    """
    Test suite for the `grapple.utils.resolve_site()` utility method.
    """

    def test_success_with_id(self):
        """
        Ensure passing a valid `id` returns the correct `Site` object.
        """

        site = wagtail_factories.SiteFactory(id=1)

        self.assertEqual(resolve_site(id=1), site)

    def test_success_with_ambiguous_hostname(self):
        """
        Ensure passing a valid `hostname` without port returns the correct
        `Site` object when there is only one Site with the same hostname.
        """

        site = wagtail_factories.SiteFactory(hostname="example.com")

        self.assertEqual(
            resolve_site(hostname="example.com", hostname_filter_name="hostname"),
            site,
        )

    def test_success_with_hostname_and_port(self):
        """
        Ensure passing a valid `hostname` with port returns the correct `Site`
        object.
        """

        site = wagtail_factories.SiteFactory(hostname="example.com", port="1000")

        self.assertEqual(
            resolve_site(hostname="example.com:1000", hostname_filter_name="hostname"),
            site,
        )

    def test_graphqlerror_when_hostname_is_ambiguous(self):
        """
        Ensure a `GraphQLError` is returned when passing an ambiguous
        `hostname`.
        """

        wagtail_factories.SiteFactory(hostname="example.com", port="1000")
        wagtail_factories.SiteFactory(hostname="example.com", port="2000")

        with self.assertRaisesRegex(
            GraphQLError, "Try including a port number to disambiguate"
        ):
            resolve_site(hostname="example.com", hostname_filter_name="hostname")

    def test_response_is_none_when_no_sites_match_hostname(self):
        """
        Ensure `None` is returned when passing a `hostname` that doesn't match
        any `Site`s.
        """

        wagtail_factories.SiteFactory(hostname="example.com")

        self.assertEqual(
            resolve_site(hostname="not.example.com", hostname_filter_name="hostname"),
            None,
        )

    def test_must_provide_id_or_hostname(self):
        """
        Ensure resolve_site() warns if used without `id` or `hostname`.
        """

        with self.assertRaisesRegex(TypeError, "neither were passed"):
            resolve_site()

    def test_cannot_provide_id_and_hostname(self):
        """
        Ensure resolve_site() warns if used with `id` and `hostname`.
        """

        with self.assertRaisesRegex(ValueError, "both were passed"):
            resolve_site(
                id=1000, hostname="example.com", hostname_filter_name="hostname"
            )

    def test_must_provide_hostname_filter_name_if_using_hostname(self):
        """
        Ensure resolve_site() warns if `hostname` is used without
        `hostname_filter_name`.
        """

        with self.assertRaisesRegex(TypeError, "hostname_filter_name"):
            resolve_site(hostname="example.com")
