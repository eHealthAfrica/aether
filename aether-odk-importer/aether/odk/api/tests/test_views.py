import uuid

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

    def test__xform__filters(self):
        self.xform.delete()  # remove default survey
        mapping_ids = {i: uuid.uuid4() for i in range(4)}
        self.helper_create_xform(mapping_id=mapping_ids[0])
        self.helper_create_xform(mapping_id=mapping_ids[0])
        self.helper_create_xform(mapping_id=mapping_ids[1])
        self.helper_create_xform(mapping_id=mapping_ids[2])

        response = self.client.get('/xforms.json', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        url = '/xforms.json?mapping_id={}'.format(mapping_ids[0])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

        url = '/xforms.json?mapping_id={}'.format(mapping_ids[1])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = '/xforms.json?mapping_id={}'.format(mapping_ids[2])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = '/xforms.json?mapping_id={}'.format(mapping_ids[3])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    def test__surveyors__search(self):
        self.helper_create_surveyor(username='peter-pan')
        self.helper_create_surveyor(username='peter-smith')
        self.helper_create_surveyor(username='peter-doe')
        self.helper_create_surveyor(username='paul-pan')

        response = self.client.get('/surveyors.json', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        response = self.client.get('/surveyors.json?search=peter', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 3)

        response = self.client.get('/surveyors.json?search=pan', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

        response = self.client.get('/surveyors.json?search=paul', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        response = self.client.get('/surveyors.json?search=wendy', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    def test__surveyors__by_survey(self):
        mapping_ids = {i: uuid.uuid4() for i in range(4)}
        # create surveyors
        a = self.helper_create_surveyor(username='a')
        b = self.helper_create_surveyor(username='b')
        c = self.helper_create_surveyor(username='c')
        d = self.helper_create_surveyor(username='d')

        # create forms with or without surveyors
        self.xform.delete()  # remove default survey

        response = self.client.get('/surveyors.json', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        mapping_id = mapping_ids[0]
        url = '/surveyors.json?mapping_id={}'.format(mapping_id)
        self.helper_create_xform(mapping_id=mapping_id)
        self.helper_create_xform(mapping_id=mapping_id, surveyor=a)
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        mapping_id = mapping_ids[1]
        url = '/surveyors.json?mapping_id={}'.format(mapping_id)
        self.helper_create_xform(mapping_id=mapping_id, surveyor=[b, c, d])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 3)

        mapping_id = mapping_ids[2]
        url = '/surveyors.json?mapping_id={}'.format(mapping_id)
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

        mapping_id = mapping_ids[3]
        url = '/surveyors.json?mapping_id={}'.format(mapping_id)
        self.helper_create_xform(mapping_id=mapping_id)
        self.helper_create_xform(mapping_id=mapping_id, surveyor=b)
        self.helper_create_xform(mapping_id=mapping_id, surveyor=b)
        self.helper_create_xform(mapping_id=mapping_id, surveyor=[b, c])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)
