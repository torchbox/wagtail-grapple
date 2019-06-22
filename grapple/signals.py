import django.dispatch
from django.dispatch import Signal, receiver

preview_update = Signal(providing_args=["token"])
