from django.apps import apps
from django.test import TestCase


class AppsTests(TestCase):

    def test_app_config(self):
        self.assertEquals(apps.get_app_config('gather').verbose_name, 'Gather')
