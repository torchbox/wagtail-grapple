import graphene_django_optimizer as gql_optimizer
from promise import Promise
from functools import partial
from promise.dataloader import DataLoader


class GenericModelLoader(DataLoader):
    model = None
    qs = None
    all_results_loaded = False

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.qs = model.objects.all()

    def batch_load_fn(self, keys):
        # Effieciently query database
        qs = self.qs.filter(id__in=keys)
        items = {item.id: item for item in qs}

        # Return matching elements
        return Promise.resolve([items.get(item_id) for item_id in keys])

    def load(self, key=None, info=None):
        if info:
            # Optimise the query before calling the superclass method
            self.qs = gql_optimizer.query(self.qs, info)
        return super().load(key)

    # Equivelent to Model.objects.all() but valuee are cached.
    def load_all(self, info):
        # If caching and there is a cache-hit, return all cached Promises.
        if self.cache:
            cached_keys = self._promise_cache.keys()
            if self.all_results_loaded:
                return self.load_many(cached_keys)

        # Optimise the query based on GraphQL AST
        self.qs = gql_optimizer.query(self.qs, info)

        # Otherwise, produce a Promise for each db result.
        promises = []
        existing_keys = [l.key for l in self._queue]

        # Query keys we haven't already batched
        for result in self.qs.all():
            cache_key = self.get_cache_key(result.id)
            promise = Promise.resolve(result)
            promises.append(promise)
            if self.cache:
                self._promise_cache[cache_key] = promise

        # Return all the models.
        self.all_results_loaded = True
        return Promise.all(promises)


# Return a model loader than binds to a loaders store (should be attached to Request object).
def create_model_loader(loaders):
    def model_loader(model):
        # Check if already created a loader for that model
        existing_loader = loaders.get(model, None)
        if existing_loader is not None:
            return existing_loader

        # Else create, save and return one.
        loaders[model] = GenericModelLoader(model)
        return loaders[model]

    return model_loader
