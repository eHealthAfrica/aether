from django.urls import reverse
from rest_framework import status

from . import CustomTestCase


class ViewsTests(CustomTestCase):

    def setUp(self):
        super(ViewsTests, self).setUp()
        self.helper_create_user()
        self.xform = self.helper_create_xform()
        self.formIdXml = '<formID>%s</formID>' % self.xform.id_string
        self.url_get = reverse('xform-get-xml_data', kwargs={'pk': self.xform.id})
        self.url_list = reverse('xform-list-xml')

    def test__form_get__none(self):
        url = reverse('xform-get-xml_data', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__form_get__no_surveyors(self):
        response = self.client.get(self.url_get, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

    def test__form_get__one_surveyor(self):
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()
        response = self.client.get(self.url_get, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test__form_get__as_surveyor(self):
        self.xform.surveyors.add(self.user)
        self.xform.save()
        response = self.client.get(self.url_get, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

    def test__form_get__as_superuser(self):
        self.helper_create_superuser()
        # with at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()

        response = self.client.get(self.url_get, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

    def test__form_list(self):
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__form_list__no_surveyors(self):
        # if no granted surveyors...
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'current user is granted surveyor')

    def test__form_list__one_surveyor(self):
        # if at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.formIdXml,
                         response.content.decode(),
                         'current user is not granted surveyor')

    def test__form_list__as_surveyor(self):
        self.xform.surveyors.add(self.user)
        self.xform.save()
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'current user is granted surveyor')

    def test__form_list__as_superuser(self):
        self.helper_create_superuser()
        # with at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()

        response = self.client.get(self.url_list, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'superusers are granted surveyors')
