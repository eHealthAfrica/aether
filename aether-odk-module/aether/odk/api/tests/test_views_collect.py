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

from python_digest import build_authorization_request
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from . import CustomTestCase


@override_settings(MULTITENANCY=False)
class CollectViewsTests(CustomTestCase):

    def setUp(self):
        super(CollectViewsTests, self).setUp()
        self.surveyor = self.helper_create_surveyor()
        self.xform = self.helper_create_xform(with_media=True, with_version=False)
        self.formIdXml = '<formID>%s</formID>' % self.xform.form_id
        self.url_get_form = self.xform.download_url
        self.url_get_media = self.xform.manifest_url
        self.url_get_media_content = self.xform.media_files.first().download_url
        self.url_list = reverse('xform-list-xml')

    def test__is_not_surveyor(self):
        self.helper_create_user()

        response = self.client.get(self.url_list, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_form, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_media, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_media_content, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__is_superuser(self):
        self.helper_create_superuser()

        response = self.client.get(self.url_list, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_form, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_media, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url_get_media_content, **self.headers_admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__form_get__none(self):
        url = reverse('xform-get-download', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('xform-get-manifest', kwargs={'pk': 0})
        response = self.client.get(url, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__form_get__no_surveyors(self):
        response = self.client.get(self.url_get_form, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

        response = self.client.get(self.url_get_media, secure=False, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(':8443', content, 'expect 8443 port to be set to default with http')

        response = self.client.get(self.url_get_media, secure=True, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn(':8443', content, 'expect 8443 port not to be set with https')

        server_info = {
            'SERVER_PORT': '81',
        }
        server_info.update(self.headers_surveyor)
        response = self.client.get(
            self.url_get_media,
            secure=True,
            **server_info
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn(':8443', content)
        self.assertIn(':81', content, 'expect explicit port to be kept with https')

        response = self.client.get(
            self.url_get_media,
            secure=False,
            **server_info
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(':8443', content)
        self.assertNotIn(':81', content,
                         'expect explicit port to be replaced by 8843 with http')

    def test__form_get__one_surveyor(self):
        self.xform.surveyors.add(self.helper_create_surveyor(username='surveyor2'))

        response = self.client.get(self.url_get_form, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.url_get_media, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.url_get_media_content, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test__form_get__as_surveyor(self):
        self.xform.surveyors.add(self.surveyor)

        self.assertEqual(self.xform.download_url, self.url_get_form)
        self.assertEqual(self.xform.manifest_url, self.url_get_media)

        response = self.client.get(self.url_get_form, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), self.xform.xml_data)

        response = self.client.get(self.url_get_media, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url_get_media_content, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="sample.txt"')
        self.assertEqual(response.content, b'abc')

        # change xform version
        self.xform.version = self.xform.version + '99'
        self.xform.save()

        self.assertNotEqual(self.xform.download_url, self.url_get_form)
        self.assertNotEqual(self.xform.manifest_url, self.url_get_media)

        # pretend to get an old version
        response = self.client.get(self.url_get_form, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url_get_media, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__form_list(self):
        response = self.client.get(self.url_list, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list')
        self.assertIn('<manifestUrl>', content, 'expect manifest url with media files')
        self.assertNotIn('<descriptionText>', content, 'expect no descriptions without verbose')
        self.assertIn(':8443', content, 'expect 8443 port to be set to default with http')

        response = self.client.get(self.url_list, secure=True, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn(':8443', content, 'expect 8443 port not to be set with https')

        server_info = {
            'SERVER_PORT': '81',
        }
        server_info.update(self.headers_surveyor)
        response = self.client.get(
            self.url_list,
            secure=True,
            **server_info
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn(':8443', content)
        self.assertIn(':81', content, 'expect explicit port to be kept with https')

        response = self.client.get(
            self.url_list,
            secure=False,
            **server_info
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(':8443', content)
        self.assertNotIn(':81', content,
                         'expect explicit port to be replaced by 8443 with http')

        response = self.client.get(
            self.url_list + '?verbose=true&formID=' + self.xform.form_id,
            **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list with formID')
        self.assertIn('<manifestUrl>', content, 'expect manifest url with media files')
        self.assertIn('<descriptionText>', content, 'expect description with verbose')

        self.xform.media_files.all().delete()
        self.assertEqual(self.xform.media_files.count(), 0)
        response = self.client.get(
            self.url_list + '?formID=' + self.xform.form_id,
            **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn(self.formIdXml, content, 'expect form in list with formID')
        # without media files there is no manifest url
        self.assertNotIn('<manifestUrl>', content, 'expect no manifest url without media files')

        response = self.client.get(
            self.url_list + '?formID=I_do_not_exist', **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertNotIn('<xform>', content, 'expect no forms in list')

    def test__form_list__no_surveyors(self):
        # if no granted surveyors...
        response = self.client.get(self.url_list, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'current user is granted surveyor')

    def test__form_list__one_surveyor(self):
        # if at least one surveyor
        self.xform.surveyors.add(self.helper_create_surveyor(username='surveyor2'))
        response = self.client.get(self.url_list, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.formIdXml,
                         response.content.decode(),
                         'current user is not granted surveyor')

    def test__form_list__as_surveyor(self):
        self.xform.surveyors.add(self.surveyor)
        response = self.client.get(self.url_list, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.formIdXml,
                      response.content.decode(),
                      'current user is granted surveyor')

    def test__digest_auth(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Digest realm="***", nonce="***", opaque="***"
        auth_type, auth_info = response.get('WWW-Authenticate').split(None, 1)
        digest_auth = dict()
        for h in auth_info.split(','):
            key, value = h.split('=')
            digest_auth[key.strip()] = value[1:-1]

        wrong_password = build_authorization_request(
            username=self.surveyor.username,
            password='wrong-password',
            realm=digest_auth['realm'],
            method='GET',
            uri=self.url_list,
            nonce=digest_auth['nonce'],
            opaque=digest_auth['opaque'],
            nonce_count=0,
            request_digest=None,
            client_nonce=None,
        )
        response = self.client.get(self.url_list, **{'HTTP_AUTHORIZATION': wrong_password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        header = build_authorization_request(
            username=self.surveyor.username,
            password='surveyorsurveyor',
            realm=digest_auth['realm'],
            method='GET',
            uri=self.url_list,
            nonce=digest_auth['nonce'],
            opaque=digest_auth['opaque'],
            nonce_count=0,
            request_digest=None,
            client_nonce=None,
        )
        response = self.client.get(self.url_list, **{'HTTP_AUTHORIZATION': header})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
