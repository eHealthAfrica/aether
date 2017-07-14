from django.apps import AppConfig


class CoreConfig(AppConfig):  # pragma: no cover
    name = 'core'

    def ready(self):
        ''' activates signals!!! '''
        from . import signals  # flake8: noqa
