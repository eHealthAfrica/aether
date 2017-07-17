from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import XForm


class ApiAdminTests(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()

    def test__post__empty(self):
        response = self.client.post(
            reverse('admin:api_xform_add'),
            {'description': 'some text', 'gather_core_survey_id': 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xml_data__validation_error(self):
        xml_data_wrong = '''
            <h:html
                xmlns="http://www.w3.org/2002/xforms"
                xmlns:ev="http://www.w3.org/2001/xml-events"
                xmlns:h="http://www.w3.org/1999/xhtml"
                xmlns:jr="http://openrosa.org/javarosa"
                xmlns:orx="http://openrosa.org/xforms"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">

              <h:head>
        '''

        response = self.client.post(
            reverse('admin:api_xform_add'),
            {'xml_data': xml_data_wrong, 'description': 'some text', 'gather_core_survey_id': 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xls_file(self):
        # TODO: don't hardcode path
        with open('/code/api/tests/demo-xlsform.xls', 'rb') as f:
            response = self.client.post(
                reverse('admin:api_xform_add'),
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
        xml_data = '''
            <h:html
                xmlns="http://www.w3.org/2002/xforms"
                xmlns:ev="http://www.w3.org/2001/xml-events"
                xmlns:h="http://www.w3.org/1999/xhtml"
                xmlns:jr="http://openrosa.org/javarosa"
                xmlns:orx="http://openrosa.org/xforms"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">

              <h:head>
                <h:title>xForm - Test</h:title>
                <model>
                  <instance>
                    <None id="xform-id-test">
                      <starttime/>
                      <endtime/>
                      <deviceid/>
                      <meta>
                        <instanceID/>
                      </meta>
                    </None>
                  </instance>
                  <instance id="other-entry">
                  </instance>
                </model>
              </h:head>
              <h:body>
              </h:body>
            </h:html>
        '''

        response = self.client.post(
            reverse('admin:api_xform_add'),
            {'xml_data': xml_data, 'description': 'some text', 'gather_core_survey_id': 1},
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.gather_core_survey_id, 1)
