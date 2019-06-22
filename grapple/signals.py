from django.dispatch import Signal

preview_update = Signal(providing_args=["token"])
