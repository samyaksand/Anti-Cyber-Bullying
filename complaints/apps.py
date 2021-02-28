from django.apps import AppConfig


class ComplaintsConfig(AppConfig):
    name = 'complaints'

    def ready(self):
        from . import signals  # noqa
