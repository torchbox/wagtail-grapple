import graphene

from grapple.types.interfaces import PageInterface


class CustomInterface(graphene.Interface):
    custom_text = graphene.String()


class CustomPageInterface(PageInterface):
    custom_text = graphene.String()
