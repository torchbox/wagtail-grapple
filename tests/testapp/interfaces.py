import graphene


class CustomInterface(graphene.Interface):
    custom_text = graphene.String()
