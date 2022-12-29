from datetime import date

from django.test import TestCase
from testapp.models import BlogPage, HomePage

from grapple.types.pages import get_preview_page


class TestUnsavedPagePreview(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.home = HomePage.objects.first()
        self.page = BlogPage(
            title="Unsaved Page", slug="unsaved-page", date=date(2020, 1, 1)
        )
        # mock an unsaved page
        # there must be a better way
        # using the form libs
        self.page._cached_parent_obj = self.home
        self.page.path = "000100010001"
        self.page.steplen = 4
        self.preview = self.page.create_page_preview()
        self.token = self.preview.token

    def test_get_preview_page(self):
        self.assertEqual(self.page.pk, None)
        preview = get_preview_page(self.token)
        self.assertEqual(preview.title, self.page.title)
        self.assertEqual(preview.title, self.page.title)
        self.assertEqual(preview.slug, self.page.slug)


class TestSavedPagePreview(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.home = HomePage.objects.first()
        self.page = BlogPage(title="Saved Page", slug="Saved-page", date="2020-01-01")
        self.home.add_child(instance=self.page)
        self.preview = self.page.create_page_preview()
        self.token = self.preview.token

    def test_get_preview_page(self):
        preview = get_preview_page(self.token)
        self.assertEqual(preview.title, self.page.title)
        self.assertEqual(preview.slug, self.page.slug)
        self.assertEqual(preview.id, self.page.id)
