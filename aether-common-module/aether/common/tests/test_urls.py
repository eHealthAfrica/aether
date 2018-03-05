from django.test import TestCase
from django.urls import reverse

from aether.common.conf import settings


class UtilsTest(TestCase):

    def test__urls__health(self):
        self.assertEqual(
            reverse('health'),
            '/health',
            'There is a "/health" endpoint'
        )

    def test__urls__accounts_login(self):
        self.assertEqual(
            reverse('rest_framework:login'),
            settings.KONG_PREFIX + '/accounts/login/',
            'There is a "/accounts/login/" endpoint'
        )

    def test__urls__accounts_logout(self):
        self.assertEqual(
            reverse('rest_framework:logout'),
            settings.KONG_PREFIX + '/accounts/logout/',
            'There is a "/accounts/logout/" endpoint'
        )

    def test__urls__accounts_token(self):
        self.assertEqual(
            reverse('token'),
            settings.KONG_PREFIX + '/accounts/token',
            'There is a "/accounts/token" endpoint'
        )

    def test__urls__check_core(self):
        self.assertEqual(
            reverse('check-kernel'),
            '/check-kernel',
            'There is a "/check-kernel" endpoint'
        )

    def test__urls__media(self):
        self.assertEqual(
            reverse('media', kwargs={'path': 'path/to/somewhere'}),
            '/media/path/to/somewhere',
            'There is a "/media" endpoint'
        )

    def test__urls__media_basic(self):
        self.assertEqual(
            reverse('media-basic', kwargs={'path': 'path/to/somewhere'}),
            '/media-basic/path/to/somewhere',
            'There is a "/media-basic" endpoint'
        )
