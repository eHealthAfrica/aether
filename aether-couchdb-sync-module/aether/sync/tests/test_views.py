from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status


class TestViews(TestCase):

    def test__health_check(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})
