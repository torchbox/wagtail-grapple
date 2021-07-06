"""
Settings for Wagtail Grapple are all namespaced in the GRAPPLE setting.
For example your project's `settings.py` file might look like this:
GRAPPLE = {
    'APPS': ['home'],
    'ADD_SEARCH_HIT': True,
}
This module provides the `grapple_settings` object, that is used to access
Wagtail Grapple settings, checking for user settings first, then falling
back to the defaults.
"""
from django.conf import settings
from django.test.signals import setting_changed


DEFAULTS = {
    "APPS": [],
    "AUTO_CAMELCASE": True,
    "ALLOWED_IMAGE_FILTERS": None,
    "EXPOSE_GRAPHIQL": False,
    "ADD_SEARCH_HIT": False,
    "PAGE_SIZE": 10,
    "MAX_PAGE_SIZE": 100,
}


class GrappleSettings:
    """
    A settings object that allows Wagtail Grapple settings to be accessed as
    properties. For example:
        from grapple.settings import grapple_settings
        print(grapple_settings.APPS)
    Note:
    This is an internal class that is only compatible with settings namespaced
    under the GRAPPLE name. It is not intended to be used by 3rd-party
    apps, and test helpers like `override_settings` may not work as expected.
    """

    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "GRAPPLE", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid Grapple setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


grapple_settings = GrappleSettings(None, DEFAULTS)


def reload_grapple_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "GRAPPLE":
        grapple_settings.reload()


setting_changed.connect(reload_grapple_settings)
