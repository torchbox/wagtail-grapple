from django.apps import AppConfig


class Grapple(AppConfig):
    name = "grapple"

    # def ready(self):
    #     from .actions import import_apps
    #     from .types.streamfield import register_streamfield_blocks

    #     """
    #     Import all the django apps defined in django settings then process each model
    #     in these apps and create graphql node types from them.
    #     """
    #     import_apps()
    #     register_streamfield_blocks()
