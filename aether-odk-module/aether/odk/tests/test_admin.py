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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.urls import reverse

from ..api.tests import CustomTestCase
from ..api.models import XForm


class AdminTests(CustomTestCase):

    def setUp(self):
        super(AdminTests, self).setUp()
        self.helper_create_superuser()
        self.url = reverse('admin:odk_xform_add')

        self.project = self.helper_create_project()
        self.PROJECT_ID = self.project.project_id

    def test__post__empty(self):
        response = self.client.post(
            self.url,
            {'description': 'some text', 'project': self.PROJECT_ID},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xml_data__validation_error(self):
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['xform']['xml-err'],
                'description': 'some text',
                'project': self.PROJECT_ID,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 0)

    def test__post__xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as fp:
            response = self.client.post(
                self.url,
                {'xml_file': fp, 'description': 'some text', 'project': self.PROJECT_ID},
            )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'my-test-form')
        self.assertEqual(instance.title, 'My Test Form')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

    def test__post__xml_file(self):
        with open(self.samples['xform']['file-xml'], 'rb') as fp:
            response = self.client.post(
                self.url,
                {'xml_file': fp, 'description': 'some text', 'project': self.PROJECT_ID},
            )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'my-test-form')
        self.assertEqual(instance.title, 'My Test Form')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

    def test__post__xml_data(self):
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)
        self.assertEqual(instance.surveyors.count(), 0, 'no granted surveyors')
        self.assertTrue(instance.is_surveyor(self.admin), 'superusers are always granted surveyors')

    def test__post__surveyors(self):
        surveyor = self.helper_create_surveyor()
        response = self.client.post(
            self.url,
            {
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'surveyors': [surveyor.id],
            },
        )
        self.assertEqual(response.status_code, 302)  # redirected to list
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

        self.assertEqual(instance.surveyors.count(), 1)
        self.assertIn(surveyor, instance.surveyors.all())
        self.assertTrue(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(self.admin))
