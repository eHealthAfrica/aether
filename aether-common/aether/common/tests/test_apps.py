from django.apps import apps
from django.test import TestCase


class AppsTests(TestCase):

    def test_app_config(self):
        self.assertEquals(
            # this is only valid in tests, the correct name is `aether.common`
            apps.get_app_config('common').verbose_name,
            'Aether common module'
        )
