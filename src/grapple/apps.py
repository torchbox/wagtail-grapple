from django.apps import AppConfig


class Grapple(AppConfig):
    name = "grapple"

    def ready(self):
        """
        Import all the django apps defined in django settings then process each model
        in these apps and create graphql node types from them.
        """
        from .actions import import_apps, load_type_fields
        from .types.streamfield import register_streamfield_blocks

        import_apps()
        load_type_fields()
        register_streamfield_blocks()
