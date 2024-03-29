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
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings

from rest_framework.serializers import ValidationError

from . import CustomTestCase
from ..models import XForm
from ..serializers import SurveyorSerializer, XFormSerializer, MediaFileSerializer


@override_settings(MULTITENANCY=False)
class SerializersTests(CustomTestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()
        self.request = RequestFactory().get('/')

    def test_xform_serializer__no_files(self):
        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)
        xform = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test xml data',
                'xml_data': self.samples['xform']['raw-xml'],
            },
            context={'request': self.request},
        )
        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'My Test Form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:html', xform.data['xml_data'])
        self.assertIn('<h:head>', xform.data['xml_data'])
        self.assertIn('<h:body>', xform.data['xml_data'])

    def test_xform_serializer__no_unique(self):
        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)

        xform_1 = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test xml data',
                'xml_data': self.samples['xform']['raw-xml'],
            },
            context={'request': self.request},
        )
        self.assertTrue(xform_1.is_valid(), xform_1.errors)
        xform_1.save()

        # create the same xForm again
        xform_2 = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test xml data',
                'xml_data': self.samples['xform']['raw-xml'],
            },
            context={'request': self.request},
        )
        self.assertFalse(xform_2.is_valid(), xform_2.errors)
        self.assertIn('Xform with this Project, XForm ID and XForm version already exists.',
                      xform_2.errors['__all__'])

        # update the xform
        instance = XForm.objects.get(pk=xform_1.data['id'])
        self.assertEqual(instance.description, 'test xml data')

        xform_3 = XFormSerializer(
            instance,
            data={
                'project': project_id,
                'description': 'test xml data 2',
                'xml_data': self.samples['xform']['raw-xml'],
            },
            context={'request': self.request},
        )
        self.assertTrue(xform_3.is_valid(), xform_3.errors)
        xform_3.save()
        instance.refresh_from_db()
        self.assertEqual(instance.description, 'test xml data 2')

    def test_xform_serializer__with_xml_file(self):
        with open(self.samples['xform']['file-xml'], 'rb') as data:
            content = SimpleUploadedFile('xform.xml', data.read())

        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)
        xform = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test xml file',
                'xml_file': content,
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'My Test Form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as data:
            content = SimpleUploadedFile('xform.xls', data.read())

        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)
        xform = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test xls file',
                'xml_file': content,
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'My Test Form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_wrong_file(self):
        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)
        xform = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test wrong file: Missing required tags',
                'xml_file': SimpleUploadedFile('xform.xml', b'<html></html>'),
            },
            context={'request': self.request},
        )

        self.assertFalse(xform.is_valid(), xform.errors)
        self.assertIn('xml_file', xform.errors)
        self.assertIn('Missing required tags:', xform.errors['xml_file'][0])

    def test_xform_serializer__with_wrong_xml_data(self):
        project_id = self.helper_create_uuid()
        self.helper_create_project(project_id=project_id)
        xform = XFormSerializer(
            data={
                'project': project_id,
                'description': 'test wrong data: Missing required tags',
                'xml_data': '<html></html>',
            },
            context={'request': self.request},
        )

        self.assertFalse(xform.is_valid(), xform.errors)
        self.assertIn('xml_data', xform.errors)
        self.assertIn('Missing required tags:', xform.errors['xml_data'][0])

    def test_media_file_serializer__no_name(self):
        project_id = self.helper_create_uuid()
        xform = self.helper_create_xform(project_id=project_id)

        media_file = MediaFileSerializer(
            data={
                'xform': xform.pk,
                'media_file': SimpleUploadedFile('audio.wav', b'abc'),
            },
            context={'request': self.request},
        )

        self.assertTrue(media_file.is_valid(), media_file.errors)
        media_file.save()
        self.assertEqual(media_file.data['name'], 'audio.wav', 'take name from file')
        self.assertEqual(media_file.data['md5sum'], '900150983cd24fb0d6963f7d28e17f72')

    def test_surveyor_serializer__no_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        with self.assertRaises(ValidationError) as ve:
            user.save()
        self.assertIn('This field is required.', str(ve.exception), ve)

    def test_surveyor_serializer__empty_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '',
            },
            context={'request': self.request},
        )
        self.assertFalse(user.is_valid(), user.errors)
        self.assertEqual(user.errors['password'][0].code, 'blank')
        self.assertEqual(str(user.errors['password'][0]),
                         'This field may not be blank.')

    def test_surveyor_serializer__weak_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '0123456',
            },
            context={'request': self.request},
        )
        self.assertFalse(user.is_valid(), user.errors)

        self.assertEqual(user.errors['password'][0].code, 'password_too_short')
        self.assertEqual(str(user.errors['password'][0]),
                         'This password is too short. It must contain at least 10 characters.')

        self.assertEqual(user.errors['password'][1].code, 'password_too_common')
        self.assertEqual(str(user.errors['password'][1]),
                         'This password is too common.')

        self.assertEqual(user.errors['password'][2].code, 'password_entirely_numeric')
        self.assertEqual(str(user.errors['password'][2]),
                         'This password is entirely numeric.')

    def test_surveyor_serializer__strong_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '~t]:vS3Q>e{2k]CE',
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        self.assertNotIn(
            'password', user.data,
            'Password is not included within the serializer data')

    def test_surveyor_serializer__create_and_update(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '~t]:vS3Q>e{2k]CE',
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        user_obj = get_user_model().objects.get(pk=user.data['id'])
        hashed_password = user_obj.password

        self.assertIn(self.surveyor_group, user_obj.groups.all(), 'has the group "surveyor"')

        updated_user = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test',
                'password': 'wUCK:CQsUd?)Zr93',
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user.is_valid(), updated_user.errors)
        updated_user.save()

        user_obj.refresh_from_db()
        hashed_password_1 = user_obj.password

        self.assertNotEqual(hashed_password_1, hashed_password)

        # update with the hashed password does not change the password
        updated_user_2 = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test2',
                'password': hashed_password_1,
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user_2.is_valid(), updated_user_2.errors)
        updated_user_2.save()
        user_obj.refresh_from_db()

        self.assertEqual(user_obj.username, 'test2')
        self.assertEqual(user_obj.password, hashed_password_1)

        # update without password does not change the password
        updated_user_3 = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test3',
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user_3.is_valid(), updated_user_3.errors)
        updated_user_3.save()
        user_obj.refresh_from_db()

        self.assertEqual(user_obj.username, 'test3')
        self.assertEqual(user_obj.password, hashed_password_1)

        # update with a null password does not change the password
        updated_user_4 = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test4',
                'password': None,
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user_4.is_valid(), updated_user_4.errors)
        updated_user_4.save()
        user_obj.refresh_from_db()

        self.assertEqual(user_obj.username, 'test4')
        self.assertEqual(user_obj.password, hashed_password_1)

    def test_surveyor_serializer__projects(self):
        project_id = self.helper_create_uuid()
        project = self.helper_create_project(project_id=project_id)

        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '~t]:vS3Q>e{2k]CE',
                'projects': [],
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()

        user_obj = get_user_model().objects.get(pk=user.data['id'])

        self.assertEqual(user_obj.projects.count(), 0)

        # add projects to the surveyors
        updated_user = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test',
                'projects': [project_id],
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user.is_valid(), updated_user.errors)
        updated_user.save()

        user_obj.refresh_from_db()
        self.assertIn(project, user_obj.projects.all())

        # check that if projects are not included they are not affected
        updated_user_2 = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test',
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user_2.is_valid(), updated_user_2.errors)
        updated_user_2.save()

        user_obj.refresh_from_db()
        self.assertIn(project, user_obj.projects.all())
