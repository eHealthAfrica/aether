from django.apps import AppConfig


class Config(AppConfig):
    name = 'gather2.core'
    verbose_name = 'Gather2 Core'

    def ready(self):
        ''' activates signals!!! '''
        from .api import signals  # flake8: noqa
