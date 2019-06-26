import graphene
from ..registry import registry


def SettingsQuery():
    if registry.settings:

        class SettingsObjectType(graphene.Union):
            class Meta:
                types = registry.settings.types

        class Mixin:
            setting = graphene.Field(SettingsObjectType, name=graphene.String())
            settings = graphene.List(SettingsObjectType)

            # Return just one setting base on name param.
            def resolve_setting(self, info, **kwargs):
                name = kwargs.get("name")
                for setting in registry.settings:
                    for object in setting._meta.model.objects.all():
                        if name.lower() == object._meta.model_name:
                            return object
                return None

            # Return all settings.
            def resolve_settings(self, info, **kwargs):
                snippet_objects = []
                for setting in registry.settings:
                    for object in setting._meta.model.objects.all():
                        snippet_objects.append(object)

                return snippet_objects

        return Mixin

    else:

        class Mixin:
            pass

        return Mixin
