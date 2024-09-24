import graphene

from grapple.types.interfaces import PageInterface, SnippetInterface


class AdditionalInterface(graphene.Interface):
    additional_text = graphene.String()


class CustomPageInterface(PageInterface):
    custom_text = graphene.String()


class CustomSnippetInterface(SnippetInterface):
    custom_text = graphene.String()

    def resolve_custom_text(self, info, **kwargs):
        return str(self)
