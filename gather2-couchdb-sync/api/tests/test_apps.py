from django.apps import apps
from django.test import TestCase


class AppsTests(TestCase):

    def test_app_config(self):
        self.assertEquals(apps.get_app_config('api').verbose_name, 'Gather2 Sync API')
