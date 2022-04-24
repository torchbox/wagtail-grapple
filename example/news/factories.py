import factory
import wagtail_factories

from news.models import NewsPage


class NewsPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"News post {n}")

    class Meta:
        model = NewsPage
