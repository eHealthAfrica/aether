import json
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from ..api.tests import EXAMPLE_SCHEMA, SCHEMA_FILE_SAMPLE
from ..api.models import Survey


class AdminTests(TransactionTestCase):

    def setUp(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'

        self.admin = get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()

    def test__post__empty(self):
        response = self.client.post(
            reverse('admin:core_survey_add'),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Survey.objects.count(), 0)

    def test__post__schema__validation_error(self):
        response = self.client.post(
            reverse('admin:core_survey_add'),
            {
                'name': 'some name',
                'created_by': self.admin.id,
                'schema': '{"unfinished": "obj...',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Survey.objects.count(), 0)

    def test__post__no_schema(self):
        response = self.client.post(
            reverse('admin:core_survey_add'),
            {
                'name': 'some name',
                'created_by': self.admin.id,
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(Survey.objects.count(), 1)

        instance = Survey.objects.first()
        self.assertEqual(instance.name, 'some name')
        self.assertEqual(instance.schema, '{}')

    def test__post__schema(self):
        response = self.client.post(
            reverse('admin:core_survey_add'),
            {
                'name': 'some name',
                'created_by': self.admin.id,
                'schema': json.dumps(EXAMPLE_SCHEMA),
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(Survey.objects.count(), 1)

        instance = Survey.objects.first()
        self.assertEqual(instance.name, 'some name')
        self.assertIn('title', instance.schema)
        self.assertEqual(instance.schema['title'], 'Example Schema')

    def test__post__schema_file(self):
        with open(SCHEMA_FILE_SAMPLE, 'rb') as content:
            response = self.client.post(
                reverse('admin:core_survey_add'),
                {
                    'name': 'some name',
                    'created_by': self.admin.id,
                    'schema': '{}',
                    'schema_file': content,
                },
            )

        self.assertEqual(response.status_code, 302, response)  # redirected to list
        self.assertEqual(Survey.objects.count(), 1)

        instance = Survey.objects.first()
        self.assertEqual(instance.name, 'some name')
        self.assertIn('title', instance.schema)
        self.assertEqual(instance.schema['title'], 'Example Schema')
