import wagtail_factories
from django.test import TestCase
from graphql import GraphQLError

from grapple.utils import resolve_site_by_hostname, resolve_site_by_id


class TestResolveSiteById(TestCase):
    """
    Test suite for the `grapple.utils.resolve_site_by_id()` utility method.
    """

    def test_success_with_id(self):
        """
        Ensure passing a valid `id` returns the correct `Site` object.
        """

        site = wagtail_factories.SiteFactory(id=1)

        self.assertEqual(resolve_site_by_id(id=1), site)

    def test_response_is_none_when_no_sites_match_id(self):
        """
        Ensure `None` is returned when passing a `id` that doesn't match
        any `Site`s.
        """

        wagtail_factories.SiteFactory()

        self.assertEqual(
            resolve_site_by_id(id=999999999),
            None,
        )


class TestResolveSiteByHostname(TestCase):
    """
    Test suite for the `grapple.utils.resolve_site_by_hostname()` utility
    method.
    """

    def test_success_with_ambiguous_hostname(self):
        """
        Ensure passing a valid `hostname` without port returns the correct
        `Site` object when there is only one Site with the same hostname.
        """

        site = wagtail_factories.SiteFactory(hostname="example.com")

        self.assertEqual(
            resolve_site_by_hostname(
                hostname="example.com",
                filter_name="hostname",
            ),
            site,
        )

    def test_success_with_hostname_and_port(self):
        """
        Ensure passing a valid `hostname` with port returns the correct `Site`
        object.
        """

        site = wagtail_factories.SiteFactory(hostname="example.com", port="1000")

        self.assertEqual(
            resolve_site_by_hostname(
                hostname="example.com:1000",
                filter_name="hostname",
            ),
            site,
        )

    def test_response_is_none_when_no_sites_match_hostname(self):
        """
        Ensure `None` is returned when passing a `hostname` that doesn't match
        any `Site`s.
        """

        wagtail_factories.SiteFactory(hostname="example.com")

        self.assertEqual(
            resolve_site_by_hostname(
                hostname="not.example.com",
                filter_name="hostname",
            ),
            None,
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
            resolve_site_by_hostname(
                hostname="example.com",
                filter_name="hostname",
            )
