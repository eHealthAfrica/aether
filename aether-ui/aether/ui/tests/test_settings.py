from django.conf import settings
from django.test import TestCase


class SettingsTest(TestCase):

    def test_default_variables(self):

        self.assertTrue(settings.TESTING)
        self.assertFalse(settings.DEBUG)

        self.assertFalse(settings.USE_X_FORWARDED_HOST)
        self.assertFalse(settings.USE_X_FORWARDED_PORT)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, None)

        self.assertEqual(settings.ROOT_URLCONF, 'aether.ui.urls')
        self.assertEqual(settings.WSGI_APPLICATION, 'aether.ui.wsgi.application')
        self.assertEqual(settings.APP_NAME, 'Aether')
        self.assertEqual(settings.ORG_NAME, 'eHealth Africa (Dev mode)')
        self.assertEqual(settings.AETHER_KERNEL_URL, 'http://kernel-test:9000')
        self.assertEqual(settings.AETHER_ODK_URL, 'http://odk-importer-test:9443')

        self.assertEqual(settings.AETHER_MODULES, ['odk-importer'])
        self.assertEqual(settings.AETHER_ODK, True)
