from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    def ready(self):
        print("Core app is ready")
        from . import signals  # flake8: noqa
