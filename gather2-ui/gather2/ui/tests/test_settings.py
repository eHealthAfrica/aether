from django.conf import settings
from django.test import TestCase


class SettingsTest(TestCase):

    def test_default_variables(self):

        self.assertTrue(settings.TESTING)
        self.assertFalse(settings.DEBUG)

        self.assertFalse(settings.USE_X_FORWARDED_HOST)
        self.assertFalse(settings.USE_X_FORWARDED_PORT)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, None)

        self.assertEqual(settings.ROOT_URLCONF, 'gather2.ui.urls')
        self.assertEqual(settings.WSGI_APPLICATION, 'gather2.ui.wsgi.application')
        self.assertEqual(settings.APP_NAME, 'Gather')
        self.assertEqual(settings.ORG_NAME, 'eHealth Africa (Dev mode)')
        self.assertEqual(settings.GATHER_CORE_URL, 'http://core-test:9000')
        self.assertEqual(settings.GATHER_ODK_URL, 'http://odk-importer-test:9443')

        self.assertEqual(settings.GATHER_MODULES, ['odk-importer'])
        self.assertEqual(settings.GATHER_ODK, True)
