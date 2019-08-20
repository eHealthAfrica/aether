# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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
        self.helper_create_user(login=True)

    def test__xform__filters(self):
        project_ids = {i: self.helper_create_uuid() for i in range(4)}
        self.helper_create_xform(project_id=project_ids[0], version_number=1)
        self.helper_create_xform(project_id=project_ids[0], version_number=2)
        self.helper_create_xform(project_id=project_ids[1])
        self.helper_create_xform(project_id=project_ids[2])

        response = self.client.get('/xforms.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        url = f'/xforms.json?project_id={project_ids[0]}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

        url = f'/xforms.json?project_id={project_ids[1]}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = f'/xforms.json?project_id={project_ids[2]}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        url = f'/xforms.json?project_id={project_ids[3]}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    def test__surveyors__search(self):
        self.helper_create_surveyor(username='peter-pan')
        self.helper_create_surveyor(username='peter-smith')
        self.helper_create_surveyor(username='peter-doe')
        self.helper_create_surveyor(username='paul-pan')

        response = self.client.get('/surveyors.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        response = self.client.get('/surveyors.json?search=peter')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 3)

        response = self.client.get('/surveyors.json?search=pan')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

        response = self.client.get('/surveyors.json?search=paul')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        response = self.client.get('/surveyors.json?search=wendy')
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

        response = self.client.get('/surveyors.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)

        project_id = project_ids[0]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id, version_number=1)
        self.helper_create_xform(project_id=project_id, surveyor=a, version_number=2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        project_id = project_ids[1]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id, surveyor=[b, c, d])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 3)

        project_id = project_ids[2]
        url = f'/surveyors.json?project_id={project_id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

        project_id = project_ids[3]
        url = f'/surveyors.json?project_id={project_id}'
        self.helper_create_xform(project_id=project_id, version_number=1)
        self.helper_create_xform(project_id=project_id, surveyor=b, version_number=2)
        self.helper_create_xform(project_id=project_id, surveyor=b, version_number=3)
        self.helper_create_xform(project_id=project_id, surveyor=[b, c], version_number=4)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

    def test__media_file__content(self):
        xform = self.helper_create_xform(with_media=True, with_version=False)
        media = xform.media_files.first()
        content_url = reverse('mediafile-content', kwargs={'pk': media.pk})
        self.assertEqual(content_url, f'/media-files/{media.pk}/content/')

        response = self.client.get(content_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('Content-Disposition', response)
        self.assertEqual(response.content, b'abc')

        self.client.logout()
        response = self.client.get(content_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__is_surveyor(self):
        self.helper_create_surveyor(login=True)

        response = self.client.get('/projects.json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
