import datetime

import factory
import wagtail.images.blocks as image_blocks
import wagtail_factories

from django.core.exceptions import ValidationError
from factory import fuzzy
from wagtail import blocks
from wagtail.contrib.redirects.models import Redirect

from testapp.blocks import (
    AdditionalInterfaceBlock,
    ImageGalleryBlock,
    ImageGalleryImage,
    ImageGalleryImages,
    TextWithCallableBlock,
)
from testapp.models import (
    Advert,
    Author,
    AuthorPage,
    BlogPage,
    BlogPageRelatedLink,
    MiddlewareModel,
    Person,
    SimpleModel,
)


# START: Block Factories


# TODO: Contribute upstream: https://github.com/wagtail/wagtail-factories/issues/97
class ImageBlockFactory(wagtail_factories.StructBlockFactory):
    image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)
    decorative = factory.Faker("boolean")
    alt_text = factory.Sequence(lambda n: f"Alt text {n}")

    class Meta:
        model = image_blocks.ImageBlock


class DateBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.DateBlock


class DateTimeBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.DateTimeBlock


class DecimalBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.DecimalBlock


class RichTextBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.RichTextBlock


class StreamBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.StreamBlock


class PageChooserBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = blocks.PageChooserBlock


class ImageGalleryImageFactory(wagtail_factories.StructBlockFactory):
    image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)

    class Meta:
        model = ImageGalleryImage


class ImageGalleryImagesFactory(StreamBlockFactory):
    class Meta:
        model = ImageGalleryImages


class ImageGalleryBlockFactory(wagtail_factories.StructBlockFactory):
    title = factory.Sequence(lambda n: f"Image gallery {n}")
    images = factory.SubFactory(ImageGalleryImagesFactory)

    class Meta:
        model = ImageGalleryBlock


class TextWithCallableBlockFactory(wagtail_factories.StructBlockFactory):
    text = factory.Sequence(lambda n: f"Text with callable {n}")
    integer = factory.fuzzy.FuzzyInteger(low=1, high=10)
    decimal = factory.fuzzy.FuzzyFloat(low=0.1, high=0.9)
    page = factory.SubFactory(PageChooserBlockFactory)

    class Meta:
        model = TextWithCallableBlock


class AdditionalInterfaceBlockFactory(wagtail_factories.StructBlockFactory):
    additional_text = factory.Sequence(lambda n: f"Block with additional interface {n}")

    class Meta:
        model = AdditionalInterfaceBlock


class BlogPageRelatedLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPageRelatedLink

    page = factory.SubFactory("testapp.factories.BlogPageFactory")
    name = factory.Sequence(lambda n: f"Person {n}")
    url = factory.Sequence(lambda n: f"Url {n}")


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    page = factory.SubFactory("testapp.factories.BlogPageFactory")
    role = factory.Sequence(lambda n: f"Role {n}")
    person = factory.SubFactory("testapp.factories.PersonFactory")


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    name = factory.Sequence(lambda n: f"Name {n}")
    job = factory.Sequence(lambda n: f"Job {n}")


class BlogPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"Blog post {n}")
    date = datetime.date.today()
    author = factory.SubFactory("testapp.factories.AuthorPageFactory")
    body = wagtail_factories.StreamFieldFactory(
        {
            "heading": wagtail_factories.CharBlockFactory,
            "paragraph": RichTextBlockFactory,
            "image": wagtail_factories.ImageChooserBlockFactory,
            "image_with_alt": ImageBlockFactory,
            "decimal": DecimalBlockFactory,
            "date": DateBlockFactory,
            "datetime": DateTimeBlockFactory,
            "gallery": ImageGalleryBlockFactory,
            "page": PageChooserBlockFactory,
            "text_with_callable": TextWithCallableBlockFactory,
            "objectives": wagtail_factories.ListBlockFactory(
                wagtail_factories.CharBlockFactory
            ),
        }
    )

    class Meta:
        model = BlogPage

    @factory.post_generation
    def create_links(self, create, extracted, **kwargs):
        if create:
            # Create Blog Links
            BlogPageRelatedLinkFactory.create_batch(5, page=self)
            # Create a Person
            person = PersonFactory.create()
            # Create Blog Authors
            AuthorFactory.create_batch(8, page=self, person=person)
            # Create Blog tags
            for tag in ["Tag 1", "Tag 2", "Tag 3"]:
                self.tags.add(tag)


class AuthorPageFactory(wagtail_factories.PageFactory):
    name = factory.Sequence(lambda n: f"Person {n}")

    class Meta:
        model = AuthorPage


class AdvertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Advert

    url = factory.Sequence(lambda n: f"Person {n}")
    text = fuzzy.FuzzyText()


class SimpleModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SimpleModel


class MiddlewareModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MiddlewareModel


class RedirectFactory(factory.django.DjangoModelFactory):
    """
    TODO: Replace with RedirectFactory from wagtail-factories once it exists
    @see https://github.com/wagtail/wagtail-factories/issues/82
    """

    old_path = factory.Faker("slug")
    site = factory.SubFactory(wagtail_factories.SiteFactory)
    redirect_page = factory.SubFactory(wagtail_factories.PageFactory)
    redirect_link = factory.Faker("url")
    is_permanent = factory.Faker("boolean")

    class Meta:
        model = Redirect

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Override _create() to ensure that Redirect.clean() is run in order to
        normalise `old_path`.
        @see https://github.com/wagtail/wagtail/blob/main/wagtail/contrib/redirects/models.py#L191
        """
        obj = model_class(*args, **kwargs)
        try:
            obj.clean()
        except ValidationError as ve:
            message = (
                f"Error building {model_class} with {cls.__name__}.\nBad values:\n"
            )
            for field in ve.error_dict:
                if field == "__all__":
                    message += "  __all__: obj.clean() failed\n"
                else:
                    message += f'  {field}: "{getattr(obj, field)}"\n'
            raise RuntimeError(message) from ve
        obj.save()
        return obj
