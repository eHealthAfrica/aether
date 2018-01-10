from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class ViewsTest(TestCase):

    def test__health(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})
