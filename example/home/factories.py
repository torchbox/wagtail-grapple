import datetime

import factory
import wagtail_factories
from factory import fuzzy
from home.blocks import ImageGalleryBlock, ImageGalleryImage, ImageGalleryImages
from home.models import (
    BlogPage,
    BlogPageRelatedLink,
    AuthorPage,
    Advert,
    Author,
    Person,
)
from wagtail.core import blocks


# START: Block Factories
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


class BlogPageRelatedLinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = BlogPageRelatedLink

    page = factory.SubFactory("home.factories.BlogPageFactory")
    name = factory.Sequence(lambda n: f"Person {n}")
    url = factory.Sequence(lambda n: f"Url {n}")


class AuthorFactory(factory.DjangoModelFactory):
    class Meta:
        model = Author

    page = factory.SubFactory("home.factories.BlogPageFactory")
    role = factory.Sequence(lambda n: f"Role {n}")
    person = factory.SubFactory("home.factories.PersonFactory")


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = Person

    name = factory.Sequence(lambda n: f"Name {n}")
    job = factory.Sequence(lambda n: f"Job {n}")


class BlogPageFactory(wagtail_factories.PageFactory):
    date = datetime.date.today()
    author = factory.SubFactory("home.factories.AuthorPageFactory")
    body = wagtail_factories.StreamFieldFactory(
        {
            "heading": wagtail_factories.CharBlockFactory,
            "paragraph": RichTextBlockFactory,
            "image": wagtail_factories.ImageChooserBlockFactory,
            "decimal": DecimalBlockFactory,
            "date": DateBlockFactory,
            "datetime": DateTimeBlockFactory,
            "gallery": ImageGalleryBlockFactory,
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


class AuthorPageFactory(wagtail_factories.PageFactory):
    name = factory.Sequence(lambda n: f"Person {n}")

    class Meta:
        model = AuthorPage


class AdvertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Advert

    url = factory.Sequence(lambda n: f"Person {n}")
    text = fuzzy.FuzzyText()
