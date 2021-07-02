from wagtail.core import hooks
from django.utils.crypto import get_random_string
from wagtail.core.models import Page
import graphene

from grapple.types.pages import PageInterface
from home.models import AuthorPage


class CreateAuthor(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        parent = graphene.Int()
        slug = graphene.String()

    ok = graphene.Boolean()
    author = graphene.Field(
        PageInterface,
    )

    def mutate(root, info, name, parent, slug):
        # We use uuid here in order to ensure the slug will always be unique accross tests
        author = AuthorPage(name=name, title=name, slug=slug)
        ok = True
        Page.objects.get(id=parent).add_child(instance=author)
        author.save_revision().publish()
        return CreateAuthor(author=author, ok=ok)


class Mutations(graphene.ObjectType):
    create_author = CreateAuthor.Field()
