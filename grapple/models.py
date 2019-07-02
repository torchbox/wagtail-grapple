import graphene
import datetime
import urllib
import json

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.signing import TimestampSigner
from django.shortcuts import render

from .registry import registry
from .signals import preview_update


# Classes used to define what the Django field should look like in the GQL type
class GraphQLField:
    field_name: str
    field_type: str

    def __init__(self, field_name: str, field_type: type = None):
        self.field_name = field_name
        if callable(field_type):
            self.field_type = field_type()
        else:
            self.field_type = field_type
        if field_type:
            self.field_type.source = field_name


def GraphQLString(field_name: str):
    def Mixin():
        return GraphQLField(field_name, graphene.String)
        
    return Mixin


def GraphQLFloat(field_name: str):
    def Mixin():
        return GraphQLField(field_name, graphene.Float)
        
    return Mixin


def GraphQLInt(field_name: str):
    def Mixin():
        return GraphQLField(field_name, graphene.Int)
        
    return Mixin


def GraphQLBoolean(field_name: str):
    def Mixin():
        return GraphQLField(field_name, graphene.Boolean)
        
    return Mixin


def GraphQLSnippet(field_name: str, snippet_model: str):
    class Mixin(GraphQLField):
        def __init__(self):
            (app_label, model) = snippet_model.lower().split(".")
            mdl = ContentType.objects.get(app_label=app_label, model=model)
            if mdl:
                self.field_type = registry.snippets[mdl.model_class()]
            else:
                self.field_type = graphene.String
            self.field_name = field_name

    return Mixin


def GraphQLStreamfield(field_name: str):
    from .types.streamfield import StreamFieldInterface
    def Mixin():
        return GraphQLField(field_name, graphene.List(StreamFieldInterface))
    
    return Mixin


def GraphQLImage(field_name: str):
    def Mixin():
        from .types.images import get_image_type, ImageObjectType
        return GraphQLField(field_name, graphene.Field(ImageObjectType))

    return Mixin


def GraphQLDocument(field_name: str):
    from django.conf import settings

    document_type = 'wagtaildocs.Document'
    if hasattr(settings, "WAGTAILDOCS_DOCUMENT_MODEL"):
        document_type = settings['WAGTAILDOCS_DOCUMENT_MODEL']

    return GraphQLForeignKey(field_name, document_type)


def GraphQLForeignKey(field_name: str, content_type: str, is_list: bool = False):
    class Mixin(GraphQLField):
        def __init__(self):
            app_label, model = content_type.lower().split(".")
            mdl = ContentType.objects.get(app_label=app_label, model=model)
            field_type = None

            if mdl:
                field_type = registry.models.get(mdl.model_class())

            if field_type and is_list:
                field_type = graphene.List(field_type)

            super().__init__(field_name, field_type)

    return Mixin


def GraphQLMedia(field_name: str):
    def Mixin():
        from .types.media import MediaObjectType
        return GraphQLField(field_name, MediaObjectType)

    return Mixin


class PagePreview(models.Model):
    token = models.CharField(max_length=255, unique=True)
    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE
    )
    content_json = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    def as_page(self):
        content = json.loads(self.content_json)
        page_model = ContentType.objects.get_for_id(
            content["content_type"]
        ).model_class()
        page = page_model.from_json(self.content_json)
        page.pk = content["pk"]
        return page

    @classmethod
    def garbage_collect(cls):
        yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
        cls.objects.filter(created_at__lt=yesterday).delete()


# Mixin for pages that want extra Grapple benefits:
class GrapplePageMixin:
    @classmethod
    def get_preview_signer(cls):
        return TimestampSigner(salt="headlesspreview.token")

    def create_page_preview(self):
        if self.pk is None:
            identifier = "parent_id=%d;page_type=%s" % (
                self.get_parent().pk,
                self._meta.label,
            )
        else:
            identifier = "id=%d" % self.pk

        return PagePreview.objects.create(
            token=self.get_preview_signer().sign(identifier),
            content_type=self.content_type,
            content_json=self.to_json(),
        )

    def update_page_preview(self, token):
        return PagePreview.objects.update_or_create(
            token=token,
            defaults={
                "content_type": self.content_type,
                "content_json": self.to_json(),
            },
        )

    @classmethod
    def get_preview_url(cls, token):
        return f"{settings.GRAPPLE_PREVIEW_URL}?" + urllib.parse.urlencode(
            {
                "content_type": cls._meta.app_label + "." + cls.__name__.lower(),
                "token": token,
            }
        )

    def dummy_request(self, original_request=None, **meta):
        request = super(GrapplePageMixin, self).dummy_request(
            original_request=original_request, **meta
        )
        request.GET = request.GET.copy()
        request.GET["realtime_preview"] = original_request.GET.get("realtime_preview")
        return request

    def serve_preview(self, request, mode_name):
        token = request.COOKIES.get("used-token")
        is_realtime = request.GET.get("realtime_preview")

        if token and is_realtime:
            page_preview, existed = self.update_page_preview(token)
            PagePreview.garbage_collect()
            preview_update.send(sender=GrapplePageMixin, token=token)
        else:
            page_preview = self.create_page_preview()
            page_preview.save()
            PagePreview.garbage_collect()

        response = render(
            request,
            "grapple/preview.html",
            {"preview_url": self.get_preview_url(page_preview.token)},
        )
        
        # Set cookie that auto-expires after 5mins
        response.set_cookie(key="used-token", value=page_preview.token, max_age=300)
        return response

    @classmethod
    def get_page_from_preview_token(cls, token):
        content_type = ContentType.objects.get_for_model(cls)

        # Check token is valid
        cls.get_preview_signer().unsign(token)
        try:
            return PagePreview.objects.get(
                content_type=content_type, token=token
            ).as_page()
        except BaseException:
            return
