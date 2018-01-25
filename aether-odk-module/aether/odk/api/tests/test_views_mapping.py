import json
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT
from rest_framework import status

from . import CustomTestCase


class ViewsTests(CustomTestCase):

    def setUp(self):
        super(ViewsTests, self).setUp()
        self.helper_create_user()

    def test__mapping__partial_update__without_pk(self):
        response = self.client.patch(
            '/mappings.json',
            data=json.dumps({}),
            content_type='application/json',
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test__mapping__partial_update__missing_instance(self):
        mapping_id = uuid.uuid4()
        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({}),
            content_type='application/json',
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__mapping__partial_update__without_files__missing_xforms(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({}),
            content_type='application/json',
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertEqual(content['xforms'], ['This field is required'])

    def test__mapping__partial_update__without_files__wrong_xforms(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({'xforms': [{'xml_data': self.samples['xform']['xml-err']}]}),
            content_type='application/json',
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertEqual(content['xml_data'], ['no element found: line 9, column 14'])

    def test__mapping__partial_update__without_files__creating_xforms(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({'xforms': [{'xml_data': self.samples['xform']['raw-xml']}]}),
            content_type='application/json',
            **self.headers_user,
        )

        content = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, content)
        self.assertEqual(len(content['xforms']), 1)

    def test__mapping__partial_update__without_files__removing_xforms(self):
        mapping_id = uuid.uuid4()
        self.helper_create_xform(mapping_id=mapping_id)
        self.helper_create_xform(mapping_id=mapping_id)
        self.helper_create_xform(mapping_id=mapping_id)
        self.helper_create_xform(mapping_id=mapping_id)
        response = self.client.get(
            '/mappings/{}.json'.format(mapping_id),
            **self.headers_user,
        )
        content = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, content)
        self.assertEqual(len(content['xforms']), 4)

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({'xforms': []}),
            content_type='application/json',
            **self.headers_user,
        )
        content = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, content)
        self.assertEqual(len(content['xforms']), 0)

    def test__mapping__partial_update__without_files__updating_xforms(self):
        mapping_id = uuid.uuid4()
        xform = self.helper_create_xform(mapping_id=mapping_id)
        self.assertEqual(xform.description, 'test')
        response = self.client.get(
            '/mappings/{}.json'.format(mapping_id),
            **self.headers_user,
        )
        content = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, content)
        self.assertEqual(len(content['xforms']), 1)

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=json.dumps({'xforms': [
                {
                    'id': xform.id,
                    'description': xform.description + ' and more',
                },
            ]}),
            content_type='application/json',
            **self.headers_user,
        )
        content = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK, content)
        self.assertEqual(len(content['xforms']), 1)
        self.assertEqual(content['xforms'][0]['description'], 'test and more')

    def test__mapping__partial_update__with_files__length_0(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=encode_multipart(BOUNDARY, {'files': 0}),
            content_type=MULTIPART_CONTENT,
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__mapping__partial_update__with_files(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        with open(self.samples['xform']['file-xls'], 'rb') as data:
            content_0 = SimpleUploadedFile(
                'xform.xlsx', data.read(), content_type='application/octet-stream')
        with open(self.samples['xform']['file-xml'], 'rb') as data:
            content_1 = SimpleUploadedFile('xform.xml', data.read())
        data = {
            'files': 2,
            # new
            'id_0': 0,
            'file_0': content_0,
            # updating
            'id_1': self.helper_create_xform(mapping_id=mapping_id).pk,
            'file_1': content_1,
        }

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        content = response.json()
        self.assertEqual(len(content['xforms']), 2)

    def test__mapping__partial_update__with_files__bad_content(self):
        mapping_id = uuid.uuid4()
        self.helper_create_mapping(mapping_id=mapping_id)
        with open(self.samples['xform']['file-err'], 'rb') as data:
            content_0 = SimpleUploadedFile('xform.xml', data.read())
        data = {
            'files': 1,
            'id_0': 0,
            'file_0': content_0,
        }

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        content = response.json()
        self.assertEqual(content['xml_file'], ['no element found: line 5, column 0'])

    def test__survey__partial_update__with_media_files(self):
        mapping_id = uuid.uuid4()
        xform = self.helper_create_xform(mapping_id=mapping_id)
        data = {
            'files': 1,
            # creating media file
            'id_0': xform.pk,
            'file_0': SimpleUploadedFile('audio.wav', b'abc'),
            'type_0': 'media',
        }

        self.assertEqual(xform.media_files.count(), 0)

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(xform.media_files.count(), 1)

    def test__survey__partial_update__with_media_files_wrong(self):
        mapping_id = uuid.uuid4()
        xform = self.helper_create_xform(mapping_id=mapping_id)
        data = {
            'files': 1,
            # creating media file
            'id_0': xform.pk,
            'file_0': None,
            'type_0': 'media',
        }

        self.assertEqual(xform.media_files.count(), 0)

        response = self.client.patch(
            '/mappings/{}.json'.format(mapping_id),
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            **self.headers_user,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertEqual(xform.media_files.count(), 0)
