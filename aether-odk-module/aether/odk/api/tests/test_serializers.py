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

import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from . import CustomTestCase
from ..serializers import SurveyorSerializer, XFormSerializer, MediaFileSerializer


class SerializersTests(CustomTestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()
        self.request = RequestFactory().get('/')

    def test_xform_serializer__no_files(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        xform = XFormSerializer(
            data={
                'mapping': mapping_id,
                'description': 'test xml data',
                'xml_data': self.samples['xform']['raw-xml'],
            },
            context={'request': self.request},
        )
        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_xml_file(self):
        with open(self.samples['xform']['file-xml'], 'rb') as data:
            content = SimpleUploadedFile('xform.xml', data.read())

        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        xform = XFormSerializer(
            data={
                'mapping': mapping_id,
                'description': 'test xml file',
                'xml_file': content,
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as data:
            content = SimpleUploadedFile('xform.xls', data.read())

        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        xform = XFormSerializer(
            data={
                'mapping': mapping_id,
                'description': 'test xls file',
                'xml_file': content,
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertNotEqual(xform.data['version'], '0', 'no default version number')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_wrong_file(self):
        content = SimpleUploadedFile('xform.xls', b'abcd')

        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        xform = XFormSerializer(
            data={
                'mapping': mapping_id,
                'description': 'test wrong file',
                'xml_file': content,
            },
            context={'request': self.request},
        )

        self.assertFalse(xform.is_valid(), xform.errors)

    def test_media_file_serializer__no_name(self):
        mapping_id = uuid.uuid4()
        xform = self.helper_create_xform(mapping_id=mapping_id)

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

    def test_surveyor_serializer__empty_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '',
            },
            context={'request': self.request},
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__password_eq_username(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': 'test',
            },
            context={'request': self.request},
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__short_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '0123456',
            },
            context={'request': self.request},
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__strong_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '~t]:vS3Q>e{2k]CE',
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)

    def test_surveyor_serializer__create_and_update(self):
        password = '~t]:vS3Q>e{2k]CE'
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': password,
            },
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        user_obj = get_user_model().objects.get(pk=user.data['id'])

        self.assertNotEqual(user.data['password'], password, 'no raw password')
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
        updated_user_obj = get_user_model().objects.get(pk=updated_user.data['id'])

        self.assertNotEqual(updated_user.data['password'], user.data['password'])
        self.assertIn(self.surveyor_group, updated_user_obj.groups.all())

        # update with the hashed password does not change the password
        updated_user_2 = SurveyorSerializer(
            updated_user_obj,
            data={
                'username': 'test2',
                'password': updated_user.data['password']
            },
            context={'request': self.request},
        )

        self.assertTrue(updated_user_2.is_valid(), updated_user_2.errors)
        updated_user_2.save()
        updated_user_2_obj = get_user_model().objects.get(pk=updated_user_2.data['id'])

        self.assertEqual(updated_user_2.data['username'], 'test2')
        self.assertEqual(updated_user_2.data['password'], updated_user.data['password'])
        self.assertIn(self.surveyor_group, updated_user_2_obj.groups.all())
