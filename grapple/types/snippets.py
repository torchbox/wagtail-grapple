import graphene

from ..registry import registry


class SnippetTypes:
    # SnippetObjectType class can only be created if
    # registry.snippets.types is non-empty, and should only be created
    # once (graphene complains if we register multiple type classes
    # with identical names)
    _SnippetObjectType = None

    @classmethod
    def get_object_type(cls):
        if cls._SnippetObjectType is None and registry.snippets:

            class SnippetObjectType(graphene.Union):
                class Meta:
                    types = registry.snippets.types

            cls._SnippetObjectType = SnippetObjectType
        return cls._SnippetObjectType


def SnippetsQuery():
    SnippetObjectType = SnippetTypes.get_object_type()

    if SnippetObjectType is not None:

        class Mixin:
            snippets = graphene.List(graphene.NonNull(SnippetObjectType), required=True)
            # Return all snippets.

            def resolve_snippets(self, info, **kwargs):
                snippet_objects = []
                for snippet in registry.snippets:
                    for object in snippet._meta.model.objects.all():
                        snippet_objects.append(object)

                return snippet_objects

        return Mixin

    else:

        class Mixin:
            pass

        return Mixin
