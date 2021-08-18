class RegistryItem(dict):
    @property
    def types(self) -> tuple:
        return tuple(self.values())


class Registry:
    apps = []
    pages = RegistryItem()
    documents = RegistryItem()
    images = RegistryItem()
    media = RegistryItem()
    collections = RegistryItem()
    snippets = RegistryItem()
    streamfield_blocks = RegistryItem()
    django_models = RegistryItem()
    settings = RegistryItem()
    field_middlewares = {}

    # The items in the registry that should be lazy loaded.
    lazy_types = (
        "pages",
        "documents",
        "images",
        "media",
        "collections",
        "snippets",
        "django_models",
        "settings",
    )

    # Internal use only, do not add to .models method
    schema = []

    @property
    def class_models(self) -> dict:
        models: dict = {}
        models.update(self.pages)
        models.update(self.documents)
        models.update(self.images)
        models.update(self.collections)
        models.update(self.snippets)
        models.update(self.django_models)
        models.update(self.settings)
        return models

    @property
    def models(self) -> dict:
        models: dict = {}
        models.update(self.pages)
        models.update(self.documents)
        models.update(self.images)
        models.update(self.collections)
        models.update(self.snippets)
        models.update(self.streamfield_blocks)
        models.update(self.django_models)
        models.update(self.settings)
        return models


# Singleton Registry
registry = Registry()
