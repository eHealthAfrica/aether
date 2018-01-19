from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class TestViews(TestCase):

    def test__health_check(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    def test__kernel_check(self):
        response = self.client.get(reverse('check-kernel'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.content.decode(),
            'Brought to you by eHealth Africa - good tech for hard places'
        )
