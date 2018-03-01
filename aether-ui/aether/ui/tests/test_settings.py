from django.conf import settings
from django.test import TestCase


class SettingsTest(TestCase):

    def test_default_variables(self):

        self.assertTrue(settings.TESTING)
        self.assertFalse(settings.DEBUG)

        self.assertFalse(settings.USE_X_FORWARDED_HOST)
        self.assertFalse(settings.USE_X_FORWARDED_PORT)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, None)

        self.assertEqual(settings.ROOT_URLCONF, 'ui.urls')
        self.assertEqual(settings.WSGI_APPLICATION, 'ui.wsgi.application')
        self.assertEqual(settings.APP_NAME, 'Aether UI')
        self.assertEqual(settings.AETHER_MODULES, ['kernel', 'odk'])

        self.assertIn('kernel', settings.AETHER_APPS)
        self.assertEqual(settings.AETHER_APPS['kernel']['url'], 'http://kernel-test:9000')
