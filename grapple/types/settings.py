import graphene
from graphql.error import GraphQLError
from wagtail.core.models import Site

from ..registry import registry

try:
    from wagtail.contrib.settings.models import BaseSiteSetting
except ImportError:
    # Wagtail < 4.0
    from wagtail.contrib.settings.models import BaseSetting as BaseSiteSetting


def resolve_site(hostname):
    # Optionally allow querying by port
    if ":" in hostname:
        (hostname, port) = hostname.split(":", 1)
        query = {
            "hostname": hostname,
            "port": port,
        }
    else:
        query = {
            "hostname": hostname,
        }

    try:
        return Site.objects.get(**query)
    except Site.MultipleObjectsReturned:
        raise GraphQLError(
            "Your 'site' filter value of '{}' returned multiple sites. Try adding a port number (for example: '{}:80').".format(
                hostname, hostname
            )
        )


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
                site_hostname = kwargs.pop("site", None)
                site = resolve_site(site_hostname) if site_hostname else None

                name = kwargs.get("name")
                for setting in registry.settings:
                    # If 'name' filter used, ignore any models that don't match the filter
                    if name and setting._meta.model_name != name.lower():
                        continue

                    if site and issubclass(setting._meta.model, BaseSiteSetting):
                        return setting._meta.model.objects.filter(site=site).first()
                    else:
                        return setting._meta.model.objects.first()

            # Return all settings.
            def resolve_settings(self, info, **kwargs):
                # Site filter
                # Only applies to settings that inherit from BaseSiteSetting
                site_hostname = kwargs.pop("site", None)
                site = resolve_site(site_hostname) if site_hostname else None

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
