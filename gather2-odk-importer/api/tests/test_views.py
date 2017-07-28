import base64
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status

from ..models import XForm

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


class ApiViewsTests(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        basic = b'test:testtest'
        get_user_model().objects.create_superuser(username, email, password)

        self.headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(basic).decode('ascii')
        }

    def test__form_list(self):
        response = self.client.get(reverse('form_list'), **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__download_form__none(self):
        url = reverse('download_xform', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__download_form(self):
        instance = XForm.objects.create(
            gather_core_survey_id=1,
            xml_data=xml_data,
        )
        instance.save()

        url = reverse('download_xform', kwargs={'pk': instance.id})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), xml_data)

    # def test__xform_manifest__none(self):
    #     url = reverse('xform_manifest', kwargs={'id_string': 'none'})
    #     response = self.client.get(url, **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__xform_manifest(self):
        instance = XForm.objects.create(
            gather_core_survey_id=1,
            xml_data=xml_data,
        )
        instance.save()

        url = reverse('xform_manifest', kwargs={'id_string': instance.id_string})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
