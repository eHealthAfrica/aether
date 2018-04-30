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

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase
import datetime

from .. import models


class ModelsTests(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)

    def test_models(self):

        project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
            salad_schema='a sample salad schema',
            jsonld_context='sample context',
            rdf_definition='a sample rdf definition'
        )
        self.assertEquals(str(project), project.name)
        self.assertNotEqual(models.Project.objects.count(), 0)

        mapping = models.Mapping.objects.create(
            name='sample mapping',
            definition={},
            revision='a sample revision field',
            project=project
        )
        self.assertEquals(str(mapping), mapping.name)
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertTrue(mapping.definition_prettified is not None)

        submission = models.Submission.objects.create(
            revision='a sample revision',
            map_revision='a sample map revision',
            date=datetime.datetime.now(),
            payload={},
            mapping=mapping
        )
        self.assertEquals(str(submission), '{} - {}'.format(str(mapping), submission.id))
        self.assertNotEqual(models.Submission.objects.count(), 0)
        self.assertTrue(submission.payload_prettified is not None)

        attachment = models.Attachment.objects.create(
            submission=submission,
            attachment_file=SimpleUploadedFile('sample.txt', b'abc')
        )
        self.assertEquals(str(attachment), attachment.name)
        self.assertEquals(attachment.name, 'sample.txt')
        self.assertEquals(attachment.md5sum, '900150983cd24fb0d6963f7d28e17f72')
        self.assertEquals(attachment.submission_revision, submission.revision)

        attachment_2 = models.Attachment.objects.create(
            submission=submission,
            submission_revision='next revision',
            name='sample_2.txt',
            attachment_file=SimpleUploadedFile('sample_12345678.txt', b'abcd')
        )
        self.assertEquals(str(attachment_2), attachment_2.name)
        self.assertEquals(attachment_2.name, 'sample_2.txt')
        self.assertEquals(attachment_2.md5sum, 'e2fc714c4727ee9395f324cd2e7f331f')
        self.assertEquals(attachment_2.submission_revision, 'next revision')
        self.assertNotEqual(attachment_2.submission_revision, submission.revision)

        schema = models.Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision'
        )
        self.assertEquals(str(schema), schema.name)
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertTrue(schema.definition_prettified is not None)

        projectschema = models.ProjectSchema.objects.create(
            name='sample project schema',
            mandatory_fields='a sample mandatory fields',
            transport_rule='a sample transport rule',
            masked_fields='a sample masked field',
            is_encrypted=False,
            project=project,
            schema=schema
        )
        self.assertEquals(str(projectschema), projectschema.name)
        self.assertNotEqual(models.ProjectSchema.objects.count(), 0)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload={},
            status='a sample status',
            projectschema=projectschema,
            submission=submission
        )
        self.assertEquals(str(entity), 'Entity {}'.format(entity.id))
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertTrue(entity.payload_prettified is not None)
