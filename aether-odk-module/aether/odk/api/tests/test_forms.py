# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.core.files.uploadedfile import SimpleUploadedFile

from ..tests import CustomTestCase
from ..models import XForm
from ..forms import XFormForm


class FormTests(CustomTestCase):

    def setUp(self):
        super(FormTests, self).setUp()

        self.project = self.helper_create_project()
        self.PROJECT_ID = self.project.project_id

    def test__xform__empty(self):
        form = XFormForm(
            data={
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
            },
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn('Please upload an XLS Form or an XML File, or enter the XML data.',
                      form.errors['__all__'])
        self.assertIn('This field is required.', form.errors['xml_data'])

    def test__xform__xml_data__validation_error(self):
        form = XFormForm(
            data={
                'xml_data': self.samples['xform']['xml-err'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
            },
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn('Not valid xForm definition. Reason: ', form.errors['xml_data'][0])

    def test__xform__xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as fp:
            form = XFormForm(
                data={
                    'description': 'some text',
                    'project': self.PROJECT_ID,
                    'kernel_id': self.helper_create_uuid(),
                },
                files={
                    'xml_file': SimpleUploadedFile('file.xls', fp.read(), 'application/xls'),
                },
            )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'my-test-form')
        self.assertEqual(instance.title, 'My Test Form')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

    def test__xform__xml_file(self):
        with open(self.samples['xform']['file-xml'], 'rb') as fp:
            form = XFormForm(
                data={
                    'description': 'some text',
                    'project': self.PROJECT_ID,
                    'kernel_id': self.helper_create_uuid(),
                },
                files={
                    'xml_file': SimpleUploadedFile('file.xml', fp.read(), 'text/xml'),
                },
            )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'my-test-form')
        self.assertEqual(instance.title, 'My Test Form')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

    def test__xform__xml_data(self):
        form = XFormForm(
            data={
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)
        self.assertEqual(instance.surveyors.count(), 0, 'no granted surveyors')

    def test__post__duplicated(self):
        form_1 = XFormForm(
            data={
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
            },
        )
        self.assertTrue(form_1.is_valid(), form_1.errors)
        form_1.save()
        self.assertEqual(XForm.objects.count(), 1)

        form_2 = XFormForm(
            data={
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
            },
        )
        self.assertFalse(form_2.is_valid(), form_2.errors)
        self.assertIn('Xform with this Project, XForm ID and XForm version already exists.',
                      form_2.errors['__all__'])

    def test__post__surveyors(self):
        surveyor = self.helper_create_surveyor(username='surveyor0')
        form = XFormForm(
            data={
                'xml_data': self.samples['xform']['xml-ok'],
                'description': 'some text',
                'project': self.PROJECT_ID,
                'kernel_id': self.helper_create_uuid(),
                'surveyors': [surveyor.id],
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(XForm.objects.count(), 1)

        instance = XForm.objects.first()
        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.description, 'some text')
        self.assertEqual(instance.project, self.project)

        self.assertEqual(instance.surveyors.count(), 1)
        self.assertIn(surveyor, instance.surveyors.all())
