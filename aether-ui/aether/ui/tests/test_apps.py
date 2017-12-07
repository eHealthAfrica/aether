from django.apps import apps
from django.test import TestCase


class AppsTests(TestCase):

    def test_app_config(self):
        # this is only valid in tests, the correct name is `aether.ui`
        self.assertEquals(apps.get_app_config('ui').verbose_name, 'Aether UI')
