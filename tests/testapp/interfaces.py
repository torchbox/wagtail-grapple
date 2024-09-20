import graphene

from grapple.types.interfaces import PageInterface


class AdditionalInterface(graphene.Interface):
    additional_text = graphene.String()


class CustomPageInterface(PageInterface):
    custom_text = graphene.String()
