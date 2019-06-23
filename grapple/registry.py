class RegistryItem(dict):
    @property
    def types(self) -> tuple:
        return tuple(self.values())


class Registry:
    apps = []
    pages = RegistryItem()
    documents = RegistryItem()
    images = RegistryItem()
    snippets = RegistryItem()
    streamfield_blocks = RegistryItem()
    django_models = RegistryItem()
    settings = RegistryItem()

    @property
    def models(self) -> dict:
        models: dict = {}
        models.update(self.pages)
        models.update(self.documents)
        models.update(self.images)
        models.update(self.snippets)
        models.update(self.streamfield_blocks)
        models.update(self.django_models)
        models.update(self.settings)
        return models


# Singleton Registry
registry = Registry()
