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

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import override_settings

from . import CustomTestCase
from ..models import Project, XForm, MediaFile

_URL_PREFIX = '/' + settings.ODK_COLLECT_ENDPOINT[:-1] if settings.ODK_COLLECT_ENDPOINT else ''


@override_settings(MULTITENANCY=False)
class ModelsTests(CustomTestCase):

    def test__xform__create__raises_errors(self):
        # missing required fields
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
        )
        # missing xml_data
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            project=self.helper_create_project(),
        )
        # missing project id
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            xml_data=self.samples['xform']['xml-ok'],
        )
        # xml_data with missing properties
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            project=self.helper_create_project(),
            xml_data='''
                <h:html
                        xmlns="http://www.w3.org/2002/xforms"
                        xmlns:h="http://www.w3.org/1999/xhtml">
                    <h:head>
                        <model>
                            <instance>
                            </instance>
                        </model>
                    </h:head>
                    <h:body>
                    </h:body>
                </h:html>
            ''',
        )
        # corrupted xml_data
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            project=self.helper_create_project(),
            xml_data=self.samples['xform']['xml-err'],
        )

    def test__xform__save(self):
        instance = XForm.objects.create(
            project=Project.objects.create(),
            xml_data=self.samples['xform']['xml-ok'],
        )

        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.version, 'v1')
        self.assertEqual(instance.download_url,
                         f'{_URL_PREFIX}/forms/{instance.pk}/form.xml?version=v1')
        self.assertEqual(instance.manifest_url, '', 'without media files there is no manifest url')
        self.assertEqual(str(instance), 'xForm - Test - xform-id-test')

        self.assertEqual(instance.md5sum, '5e97c4e929f64d7701804043e3b544ba')
        self.assertEqual(instance.hash, 'md5:5e97c4e929f64d7701804043e3b544ba')

        self.assertIsNotNone(instance.avro_schema)
        self.assertIsNotNone(instance.avro_schema_prettified)

    def test__xform__media(self):
        xform = XForm.objects.create(
            project=Project.objects.create(),
            xml_data=self.samples['xform']['xml-ok'],
        )
        media = MediaFile.objects.create(
            xform=xform,
            media_file=SimpleUploadedFile('sample.txt', b'abc'),
        )
        self.assertEqual(media.name, 'sample.txt', 'takes file name')
        self.assertEqual(media.md5sum, '900150983cd24fb0d6963f7d28e17f72')
        self.assertEqual(str(media), 'sample.txt')

        media.media_file = SimpleUploadedFile('sample2.txt', b'abcd')
        media.save()
        self.assertEqual(media.name, 'sample.txt', 'does not replace name')
        self.assertEqual(media.md5sum, 'e2fc714c4727ee9395f324cd2e7f331f')
        self.assertEqual(media.hash, 'md5:e2fc714c4727ee9395f324cd2e7f331f')
        self.assertEqual(media.media_file_url, media.media_file.url)
        self.assertEqual(media.download_url,
                         f'{_URL_PREFIX}/media-file/{media.pk}')
        self.assertEqual(xform.manifest_url,
                         f'{_URL_PREFIX}/forms/{xform.id}/manifest.xml?version={xform.version}',
                         'with media files there is a manifest_url')

    def test__xform__version_control(self):
        xform = XForm.objects.create(
            project=Project.objects.create(),
            xml_data=self.samples['xform']['xml-ok'],
        )
        last_version = xform.version
        last_avro_schema = xform.avro_schema
        last_kernel_id = xform.kernel_id
        self.assertEqual(last_version, 'v1')

        xform.xml_data = self.samples['xform']['xml-ok']
        xform.save()

        self.assertEqual(last_version, xform.version, 'nothing changed')
        self.assertEqual(last_avro_schema, xform.avro_schema, 'nothing changed')
        self.assertEqual(last_kernel_id, xform.kernel_id, 'nothing changed')

        last_version = xform.version
        last_avro_schema = xform.avro_schema
        last_kernel_id = xform.kernel_id

        xform.xml_data = self.samples['xform']['xml-ok-noversion']
        xform.save()

        self.assertNotEqual(last_version, xform.version, 'changed xml data')
        self.assertNotEqual(last_avro_schema, xform.avro_schema, 'changed AVRO schema')
        self.assertNotEqual(last_kernel_id, xform.kernel_id, 'changed Kernel ID')

    def test__model_methods(self):
        project = Project.objects.create()
        xform = XForm.objects.create(
            project=project,
            xml_data=self.samples['xform']['xml-ok'],
        )
        media_file = MediaFile.objects.create(
            xform=xform,
            media_file=SimpleUploadedFile('sample.txt', b'abc'),
        )

        self.assertFalse(project.is_accessible(settings.DEFAULT_REALM))
        self.assertFalse(xform.is_accessible(settings.DEFAULT_REALM))
        self.assertFalse(media_file.is_accessible(settings.DEFAULT_REALM))

        self.assertIsNone(project.get_realm())
        self.assertIsNone(xform.get_realm())
        self.assertIsNone(media_file.get_realm())
