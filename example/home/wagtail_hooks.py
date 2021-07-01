from wagtail.core import hooks
from .mutations import Mutations


@hooks.register("register_schema_mutation")
def register_author_mutation(mutation_mixins):
    mutation_mixins.append(Mutations)
