from django.apps import AppConfig


class Config(AppConfig):
    name = 'aether.kernel'
    verbose_name = 'Aether Kernel'

    def ready(self):
        ''' activates signals!!! '''
        # from .api import signals  # flake8: noqa
