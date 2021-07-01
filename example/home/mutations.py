from wagtail.core import hooks
import graphene

from home.models import AuthorPage


class CreateAuthor(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    ok = graphene.Boolean()
    author = graphene.Field(lambda: AuthorPage)

    def mutate(root, info, name):
        author = AuthorPage(name=name)
        ok = True
        return CreateAuthor(author=author, ok=ok)


@hooks.register("register_schema_mutation")
def register_author_mutation(mutation_mixins):
    mutation_mixins.append(CreateAuthor)
