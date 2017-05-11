from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from hypothesis.extra.django import TestCase

from .models import XForm


class SimpleTestCase(TestCase):
    def test_survey_smoke_test(self):
        username = 'test'
        email = 'test@example.com'
        password = 'test'

        user = User.objects.create_superuser(username, email, password)
        client = Client()
        client.login(username=user.username, password=password)

        # TODO: don't hardcode path
        with open('/code/api/demo-xlsform.xls', 'rb') as f:
            response = client.post(reverse('admin:api_xform_add'), {'xlsform': f, 'description': 'some text', 'gather_core_survey_id': 1})
        print(response.content.decode())

        assert XForm.objects.count() == 1
