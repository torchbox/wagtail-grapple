import graphene
from ..registry import registry


def SnippetsQuery():
    if registry.snippets:

        class SnippetObjectType(graphene.Union):
            class Meta:
                types = registry.snippets.types

        class Mixin:
            snippets = graphene.List(SnippetObjectType)
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
