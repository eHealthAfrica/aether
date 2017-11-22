from django.apps import AppConfig


class Config(AppConfig):
    name = 'aether.core'
    verbose_name = 'Aether Core'

    def ready(self):
        ''' activates signals!!! '''
        # from .api import signals  # flake8: noqa
