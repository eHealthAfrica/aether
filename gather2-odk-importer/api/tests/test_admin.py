from django.urls import reverse

from . import CustomTestCase
from ..models import XForm


class AdminTests(CustomTestCase):

    def setUp(self):
        super(AdminTests, self).setUp()
        self.helper_create_superuser()
        self.url = reverse('admin:api_xform_add')

    def test__post__empty(self):
        response = self.client.post(
            self.url,
            {'description': 'some text', 'gather_core_survey_id': 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xml_data__validation_error(self):
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['data']['xml-err'],
                'description': 'some text',
                'gather_core_survey_id': 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xlsform': f, 'description': 'some text', 'gather_core_survey_id': 1},
            )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'my-test-form')
        self.assertEqual(instance.title, 'my-test-form')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.gather_core_survey_id, 1)

    def test__post__xml_data(self):
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['data']['xml-ok'],
                'description': 'some text',
                'gather_core_survey_id': 1,
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.gather_core_survey_id, 1)
        self.assertEqual(instance.surveyors.count(), 0, 'no granted surveyors')
        self.assertTrue(instance.is_surveyor(self.admin), 'superusers are always granted surveyors')

    def test__post__surveyors(self):
        surveyor = self.helper_create_surveyor()
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['data']['xml-ok'],
                'description': 'some text',
                'gather_core_survey_id': 1,
                'surveyors': [surveyor.id],
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.gather_core_survey_id, 1)

        self.assertEqual(instance.surveyors.count(), 1)
        self.assertIn(surveyor, instance.surveyors.all())
        self.assertTrue(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(self.admin))
