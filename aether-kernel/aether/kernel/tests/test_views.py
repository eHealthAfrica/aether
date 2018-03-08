from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class TestViews(TestCase):

    def test__health_check(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    def test_api_pass(self):
        response = self.client.post('/token', {'client_id': 'a_test_client_id'})
        self.assertEqual(400, response.status_code)
        response = self.client.post('/token', {'username': 'testUsername', 'password': 'testPassword'})
        self.assertEqual(200, response.status_code)
        response = self.client.post('/token',
                                    {'username': 'testUsername', 'password': 'testPassword',
                                     'redirect_uri': 'http://testuri.org', 'app_name': 'test_app'})
        self.assertEqual(200, response.status_code)

    def test__urls__api_pass(self):
        self.assertEqual(
            reverse('token'),
            '/token',
            'There is a "/token" endpoint'
        )
