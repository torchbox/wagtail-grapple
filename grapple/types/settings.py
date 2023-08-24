import graphene

from graphql import GraphQLError
from wagtail.contrib.settings.models import BaseGenericSetting, BaseSiteSetting
from wagtail.models import Site

from ..registry import registry
from ..utils import resolve_site_by_hostname


def SettingsQuery():
    if registry.settings:

        class SettingsObjectType(graphene.Union):
            class Meta:
                types = registry.settings.types

        class Mixin:
            setting = graphene.Field(
                SettingsObjectType,
                name=graphene.String(),
                site=graphene.String(),
            )
            settings = graphene.List(
                graphene.NonNull(SettingsObjectType),
                required=True,
                name=graphene.String(),
                site=graphene.String(),
            )

            # Return just one setting base on name param.
            def resolve_setting(self, info, **kwargs):
                # Site filter
                # Only applies to settings that inherit from BaseSiteSetting
                site_hostname_kwarg = "site"
                site_hostname = kwargs.pop(site_hostname_kwarg, None)

                if site_hostname is not None:
                    site = resolve_site_by_hostname(
                        hostname=site_hostname,
                        filter_name=site_hostname_kwarg,
                    )
                else:
                    site = None

                name = kwargs.get("name")
                for setting in registry.settings:
                    # If 'name' filter used, ignore any models that don't match the filter
                    if name and setting._meta.model_name != name.lower():
                        continue

                    if issubclass(setting._meta.model, BaseSiteSetting):
                        if site:
                            return setting._meta.model.objects.filter(site=site).first()
                        elif Site.objects.all().count() == 1:
                            # If there's only one Site, we can reliably return
                            # the correct (i.e. only) SiteSetting.
                            return setting._meta.model.objects.first()
                        else:
                            # If there are multiple `Site`s, we don't know what
                            # data to return.
                            raise GraphQLError(
                                f"There are multiple `{name}` instances - "
                                "please include a `site` filter to disambiguate "
                                f"(e.g. `setting(name: '{name}', site='example.com')`."
                            )

                    elif issubclass(setting._meta.model, BaseGenericSetting):
                        # If it's a GenericSetting, there can only be one.
                        return setting._meta.model.objects.first()

                    return None

            # Return all settings.
            def resolve_settings(self, info, **kwargs):
                # Site filter
                # Only applies to settings that inherit from BaseSiteSetting
                site_hostname_kwarg = "site"
                site_hostname = kwargs.pop(site_hostname_kwarg, None)

                if site_hostname is not None:
                    site = resolve_site_by_hostname(
                        hostname=site_hostname,
                        filter_name=site_hostname_kwarg,
                    )
                else:
                    site = None

                name = kwargs.get("name")
                settings_objects = []
                for setting in registry.settings:
                    # If 'name' filter used, ignore any models that don't match the filter
                    if name and setting._meta.model_name != name.lower():
                        continue

                    if site and issubclass(setting._meta.model, BaseSiteSetting):
                        settings_objects.extend(
                            setting._meta.model.objects.filter(site=site)
                        )

                    else:
                        settings_objects.extend(setting._meta.model.objects.all())

                return settings_objects

        return Mixin

    else:

        class Mixin:
            pass

        return Mixin
