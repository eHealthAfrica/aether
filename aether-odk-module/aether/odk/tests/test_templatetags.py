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

from django.template import Context, Template
from django.test import TestCase, override_settings
from django.test.client import RequestFactory


from aether.odk.templatetags import odk_tags

class MediaFileMock:
    name = 'mediafile-name'
    url = 'mediafile-url'


class TestTemplateTags(TestCase):

    def render_get_file_url(self):
        media_file = MediaFileMock()
        factory = RequestFactory()
        template = (
            '{% load odk_tags %}'
            '{% get_file_url media_file %}'
        )
        request = factory.get('/')
        context = Context({
            'request': factory.get('/'),
            'media_file': media_file,
        })
        return Template(template).render(context)

    @override_settings(DJANGO_STORAGE_BACKEND='filesystem')
    def test_get_file_url__filesystem(self):
        expected = 'http://testserver/media-basic/mediafile-name'
        result = self.render_get_file_url()
        self.assertEqual(expected, result)

    @override_settings(DJANGO_STORAGE_BACKEND='s3')
    def test_get_file_url__s3(self):
        expected = MediaFileMock.url
        result = self.render_get_file_url()
        self.assertEqual(expected, result)

