from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Gather2 Core'

    def ready(self):
        ''' activates signals!!! '''
        from . import signals  # flake8: noqa
