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

import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ..models import Project, Schema
from ..forms import SchemaForm

AVRO_SAMPLE = {
    'namespace': 'org.ehealthafrica.sample',
    'name': 'Person',
    'type': 'record',
    'fields': [
        {
            'name': 'first_name',
            'type': 'string',
        },
        {
            'name': 'last_name',
            'type': 'string',
        },
        {
            'doc': 'UUID',
            'name': 'id',
            'type': 'string',
        },
    ],
}

AVRO_FILE = SimpleUploadedFile('person.avsc', json.dumps(AVRO_SAMPLE).encode('utf-8'))


class FormsTests(TestCase):

    def setUp(self):
        super(FormsTests, self).setUp()

        project = Project.objects.create(name='sample')
        self.KERNEL_ID = str(project.pk)
        self.assertEqual(Schema.objects.count(), 0)

    def test__form__empty(self):
        form = SchemaForm(
            data={
                'name': 'person',
                'project': self.KERNEL_ID,
                'kernel_id': self.KERNEL_ID,
            },
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(Schema.objects.count(), 0)
        self.assertIn('Please upload an AVRO Schema file, or enter the AVRO Schema definition.',
                      form.errors['__all__'][0])

    def test__form__without_file(self):
        form = SchemaForm(
            data={
                'name': 'person',
                'project': self.KERNEL_ID,
                'kernel_id': self.KERNEL_ID,
                'avro_schema': AVRO_SAMPLE,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(Schema.objects.count(), 1)

        instance = Schema.objects.first()
        self.assertEqual(instance.avro_schema, AVRO_SAMPLE)
        self.assertEqual(instance.name, 'person')

    def test__form__with_file(self):
        form = SchemaForm(
            data={
                'name': 'person',
                'project': self.KERNEL_ID,
                'kernel_id': self.KERNEL_ID,
                'avro_schema': None,
            },
            files={
                'avro_file': AVRO_FILE,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['avro_schema'], AVRO_SAMPLE)
        form.save()
        self.assertEqual(Schema.objects.count(), 1)

        instance = Schema.objects.first()
        self.assertEqual(instance.name, 'person')
        self.assertEqual(instance.avro_schema, AVRO_SAMPLE)

    def test__form__with_wrong_file(self):
        form = SchemaForm(
            data={
                'name': 'person',
                'project': self.KERNEL_ID,
                'kernel_id': self.KERNEL_ID,
                'avro_schema': None,
            },
            files={
                'avro_file': SimpleUploadedFile('person.avsc', b'{"name"}'),
            },
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(Schema.objects.count(), 0)
        self.assertIn("Expecting ':' delimiter: line 1 column 8 (char 7)",
                      form.errors['avro_schema'][0])
