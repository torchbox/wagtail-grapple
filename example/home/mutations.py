from wagtail.core import hooks
from wagtail.core.models import Page
import graphene

from grapple.types.pages import PageInterface
from home.models import AuthorPage


class CreateAuthor(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    ok = graphene.Boolean()
    author = graphene.Field(
        PageInterface,
    )

    def mutate(root, info, name):
        author = AuthorPage(name=name, title=name, slug=name)
        ok = True
        Page.objects.first().add_child(instance=author)
        author.save_revision().publish()
        return CreateAuthor(author=author, ok=ok)


class Mutations(graphene.ObjectType):
    create_author = CreateAuthor.Field()
