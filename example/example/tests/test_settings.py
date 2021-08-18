from django.test import TestCase, override_settings

from grapple.settings import (
    DEPRECATED_SETTINGS,
    REMOVED_SETTINGS,
    GrappleSettings,
    grapple_settings,
)


class TestSettings(TestCase):
    def test_warning_raised_on_deprecated_setting(self):
        """
        Make sure user is alerted with an warning when a deprecated setting is set.
        """
        if len(DEPRECATED_SETTINGS) > 0:
            with self.assertLogs("grapple", level="WARNING"):
                user_settings = {}
                user_settings[DEPRECATED_SETTINGS[0]] = True
                GrappleSettings(user_settings)

    def test_error_raised_on_removed_setting(self):
        """
        Make sure user is alerted with an error when a removed setting is set.
        """
        if len(REMOVED_SETTINGS) > 0:
            with self.assertRaises(RuntimeError):
                user_settings = {}
                user_settings[REMOVED_SETTINGS[0]] = True
                GrappleSettings(user_settings)

    def test_compatibility_with_override_settings(self):
        """
        Usage of grapple_settings is bound at import time:
            from grapple.settings import grapple_settings
        setting_changed signal hook must ensure bound instance is refreshed.
        """
        self.assertEquals(grapple_settings.PAGE_SIZE, 10)

        with override_settings(GRAPPLE={"PAGE_SIZE": 5}):
            self.assertEquals(grapple_settings.PAGE_SIZE, 5)

        self.assertEquals(grapple_settings.PAGE_SIZE, 10)
