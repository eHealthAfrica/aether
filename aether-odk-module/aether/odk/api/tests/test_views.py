# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from . import CustomTestCase


@override_settings(MULTITENANCY=False)
class ViewsTests(CustomTestCase):

    def setUp(self):
        super(ViewsTests, self).setUp()
        self.helper_create_user()
        self.xform = self.helper_create_xform(with_media=True, with_version=False)
        self.formIdXml = '<formID>%s</formID>' % self.xform.form_id
        self.url_get_form = self.xform.download_url
        self.url_get_media = self.xform.manifest_url
        self.url_list = reverse('xform-list-xml')

    def test__form_get__none(self):
        url = reverse('xform-get-download', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('xform-get-manifest', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__form_get__no_surveyors(self):
        response = self.client.get(self.url_get_form, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

        response = self.client.get(self.url_get_media, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__form_get__one_surveyor(self):
        self.xform.surveyors.add(self.helper_create_surveyor())

        response = self.client.get(self.url_get_form, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.url_get_media, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test__form_get__as_surveyor(self):
        self.xform.surveyors.add(self.user)

        self.assertEqual(self.xform.download_url, self.url_get_form)
        self.assertEqual(self.xform.manifest_url, self.url_get_media)

        response = self.client.get(self.url_get_form, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

        response = self.client.get(self.url_get_media, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change xform version
        self.xform.version = self.xform.version + '99'
        self.xform.save()

        self.assertNotEqual(self.xform.download_url, self.url_get_form)
        self.assertNotEqual(self.xform.manifest_url, self.url_get_media)

        # pretend to get an old version
        response = self.client.get(self.url_get_form, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url_get_media, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__form_get__as_superuser(self):
        self.helper_create_superuser()
        # with at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor())

        response = self.client.get(self.url_get_form, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

        response = self.client.get(self.url_get_media, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__form_list(self):
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list')
        self.assertIn('<manifestUrl>', content, 'expect manifest url with media files')
        self.assertNotIn('<descriptionText>', content, 'expect no descriptions without verbose')

        response = self.client.get(
            self.url_list + '?verbose=true&formID=' + self.xform.form_id,
            **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list with formID')
        self.assertIn('<manifestUrl>', content, 'expect manifest url with media files')
        self.assertIn('<descriptionText>', content, 'expect description with verbose')

        self.xform.media_files.all().delete()
        self.assertEqual(self.xform.media_files.count(), 0)
        response = self.client.get(
            self.url_list + '?formID=' + self.xform.form_id,
            **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list with formID')
        # without media files there is no manifest url
        self.assertNotIn('<manifestUrl>', content, 'expect no manifest url without media files')

        response = self.client.get(
            self.url_list + '?formID=I_do_not_exist', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn('<xform>', content, 'expect no forms in list')

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
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.formIdXml,
                         response.content.decode(),
                         'current user is not granted surveyor')

    def test__form_list__as_surveyor(self):
        self.xform.surveyors.add(self.user)
        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'current user is granted surveyor')

    def test__form_list__as_superuser(self):
        self.helper_create_superuser()
        # with at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor())

        response = self.client.get(self.url_list, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'superusers are granted surveyors')

    def test__xform__filters(self):
        self.xform.delete()  # remove default xform
        project_ids = {i: self.helper_create_uuid() for i in range(4)}
        self.helper_create_xform(project_id=project_ids[0])
        self.helper_create_xform(project_id=project_ids[0])
        self.helper_create_xform(project_id=project_ids[1])
        self.helper_create_xform(project_id=project_ids[2])

        response = self.client.get('/xforms.json', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        url = f'/xforms.json?project_id={project_ids[0]}'
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

        url = f'/xforms.json?project_id={project_ids[1]}'
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = f'/xforms.json?project_id={project_ids[2]}'
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = f'/xforms.json?project_id={project_ids[3]}'
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

    def test__surveyors__by_project(self):
        project_ids = {i: self.helper_create_uuid() for i in range(4)}
        # create surveyors
        a = self.helper_create_surveyor(username='a')
        b = self.helper_create_surveyor(username='b')
        c = self.helper_create_surveyor(username='c')
        d = self.helper_create_surveyor(username='d')

        # create xforms with or without surveyors
        self.xform.delete()  # remove default xform

        response = self.client.get('/surveyors.json', **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        project_id = project_ids[0]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id)
        self.helper_create_xform(project_id=project_id, surveyor=a)
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        project_id = project_ids[1]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id, surveyor=[b, c, d])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 3)

        project_id = project_ids[2]
        url = f'/surveyors.json?project_id={project_id}'
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

        project_id = project_ids[3]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id)
        self.helper_create_xform(project_id=project_id, surveyor=b)
        self.helper_create_xform(project_id=project_id, surveyor=b)
        self.helper_create_xform(project_id=project_id, surveyor=[b, c])
        response = self.client.get(url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)
