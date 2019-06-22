class RegistryItem(dict):
    @property
    def types(self) -> tuple:
        return tuple(self.values())

class Registry:
    pages = RegistryItem()
    documents = RegistryItem()
    images = RegistryItem()
    snippets = RegistryItem()
    streamfield_blocks = RegistryItem()

    @property
    def models(self) -> dict:
        models: dict = {}
        models.update(self.pages)
        models.update(self.documents)
        models.update(self.images)
        models.update(self.snippets)
        models.update(self.streamfield_blocks)
        return models

# Singleton Registry
registry = Registry()