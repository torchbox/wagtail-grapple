import graphene
from home.models import Advert, AuthorPage

try:
    from wagtail.models import Page
except ImportError:
    from wagtail.core.models import Page

from grapple.registry import registry
from grapple.types.pages import PageInterface
from grapple.types.rich_text import RichText


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
        # We use uuid here in order to ensure the slug will always be unique across tests
        author = AuthorPage(name=name, title=name, slug=slug)
        ok = True
        Page.objects.get(id=parent).add_child(instance=author)
        author.save_revision().publish()
        return CreateAuthor(author=author, ok=ok)


class CreateAdvert(graphene.Mutation):
    class Arguments:
        url = graphene.String(required=True)
        text = graphene.String(required=True)
        rich_text = RichText()
        extra_rich_text = RichText()

    advert = graphene.Field(registry.models[Advert])

    @classmethod
    def mutate(cls, root, info, url, text, rich_text="", extra_rich_text=""):
        advert = Advert.objects.create(
            url=url,
            text=text,
            rich_text=rich_text,
            extra_rich_text=extra_rich_text,
        )
        return CreateAdvert(advert)


class UpdateAdvert(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        url = graphene.String()
        text = graphene.String()
        rich_text = RichText()
        extra_rich_text = RichText()

    advert = graphene.Field(registry.models[Advert])

    @classmethod
    def mutate(cls, root, info, id, url="", text="", rich_text="", extra_rich_text=""):
        advert = Advert.objects.get(id=id)
        advert.url = url
        advert.text = text
        advert.rich_text = rich_text
        advert.extra_rich_text = extra_rich_text
        advert.save()
        return UpdateAdvert(advert)


class Mutations(graphene.ObjectType):
    create_author = CreateAuthor.Field()
    create_advert = CreateAdvert.Field()
    update_advert = UpdateAdvert.Field()
