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

import uuid

from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase

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
        )
        self.assertEquals(str(project), project.name)
        self.assertNotEqual(models.Project.objects.count(), 0)

        mappingset = models.MappingSet.objects.create(
            revision='a sample revision',
            name='a sample mapping set',
            schema={},
            input={},
            project=project,
        )
        self.assertEquals(str(mappingset), mappingset.name)
        self.assertNotEqual(models.MappingSet.objects.count(), 0)
        self.assertEquals(str(mappingset.project), str(project))
        self.assertIsNotNone(mappingset.input_prettified)
        self.assertIsNotNone(mappingset.schema_prettified)

        mapping = models.Mapping.objects.create(
            name='sample mapping',
            definition={},
            revision='a sample revision field',
            mappingset=mappingset,
        )
        self.assertEquals(str(mapping), mapping.name)
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertIsNotNone(mapping.definition_prettified)
        self.assertEqual(mapping.projectschemas.count(), 0, 'No entities in definition')

        submission = models.Submission.objects.create(
            revision='a sample revision',
            payload={},
            mappingset=mappingset,
        )
        self.assertNotEqual(models.Submission.objects.count(), 0)
        self.assertIsNotNone(submission.payload_prettified)
        self.assertEqual(submission.project, project, 'submission inherits mapping project')
        self.assertEqual(submission.name, 'a project name-a sample mapping set')

        attachment = models.Attachment.objects.create(
            submission=submission,
            attachment_file=SimpleUploadedFile('sample.txt', b'abc'),
        )
        self.assertEquals(str(attachment), attachment.name)
        self.assertEquals(attachment.name, 'sample.txt')
        self.assertEquals(attachment.md5sum, '900150983cd24fb0d6963f7d28e17f72')
        self.assertEquals(attachment.submission_revision, submission.revision)
        self.assertTrue(attachment.attachment_file_url.endswith(attachment.attachment_file.url))

        attachment_2 = models.Attachment.objects.create(
            submission=submission,
            submission_revision='next revision',
            name='sample_2.txt',
            attachment_file=SimpleUploadedFile('sample_12345678.txt', b'abcd'),
        )
        self.assertEquals(str(attachment_2), attachment_2.name)
        self.assertEquals(attachment_2.name, 'sample_2.txt')
        self.assertEquals(attachment_2.md5sum, 'e2fc714c4727ee9395f324cd2e7f331f')
        self.assertEquals(attachment_2.submission_revision, 'next revision')
        self.assertNotEqual(attachment_2.submission_revision, submission.revision)

        schema = models.Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision',
        )
        self.assertEquals(str(schema), schema.name)
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertIsNotNone(schema.definition_prettified)
        self.assertEqual(schema.family_name, 'sample schema')

        schema.definition = {'name': 'Person'}
        schema.save()
        self.assertEqual(schema.family_name, 'Person')

        schema.family = 'People'
        schema.save()
        self.assertEqual(schema.family_name, 'People')

        projectschema = models.ProjectSchema.objects.create(
            name='sample project schema',
            project=project,
            schema=schema,
        )
        self.assertEquals(str(projectschema), projectschema.name)
        self.assertNotEqual(models.ProjectSchema.objects.count(), 0)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload={},
            status='a sample status',
            projectschema=projectschema,
            mapping=mapping,
            submission=submission,
        )
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertIsNotNone(entity.payload_prettified)
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.name, f'{project.name}-{schema.family_name}')

        project_2 = models.Project.objects.create(
            revision='rev 1',
            name='a second project name',
        )
        projectschema_2 = models.ProjectSchema.objects.create(
            name='sample second project schema',
            is_encrypted=False,
            project=project_2,
            schema=schema,
        )
        self.assertNotEqual(entity.submission.project, projectschema_2.project)
        entity.projectschema = projectschema_2
        with self.assertRaises(IntegrityError) as ie:
            entity.save()

        self.assertIsNotNone(ie)
        self.assertIn('Submission and Project Schema MUST belong to the same Project',
                      str(ie.exception))

        # it works without submission
        entity.submission = None
        entity.save()
        self.assertEqual(entity.project, project_2, 'entity inherits projectschema project')
        self.assertEqual(entity.name, f'{project_2.name}-{schema.family_name}')

        # keeps last project
        entity.projectschema = None
        entity.save()
        self.assertEqual(entity.project, project_2, 'entity keeps project')
        self.assertEqual(entity.name, entity.project.name)

        entity.project = None
        entity.save()
        self.assertEqual(entity.name, None)

        # till new submission or new projectschema is set
        entity.project = project_2  # this is going to be replaced
        entity.submission = submission
        entity.projectschema = None
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.name, entity.submission.name)

        entity.submission = None
        entity.projectschema = projectschema
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits projectschema project')
        self.assertEqual(entity.name, f'{project.name}-{schema.family_name}')

        # try to build entity name with mapping entity entries
        projectschema_3 = models.ProjectSchema.objects.create(
            name='sample project schema 3',
            project=project,
            schema=schema,
        )

        self.assertEqual(mapping.projectschemas.count(), 0)
        mapping.definition = {
            'entities': {
                'None': str(projectschema_3.pk),
                'Some': str(entity.projectschema.pk),
            }
        }
        mapping.save()
        self.assertEqual(mapping.projectschemas.count(), 2)
        self.assertEqual(entity.name, f'{entity.project.name}-Some')

    def test_models_ids(self):

        first_id = uuid.uuid4()
        second_id = uuid.uuid4()
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(models.Project.objects.filter(pk=first_id).count(), 0)
        self.assertEqual(models.Project.objects.filter(pk=second_id).count(), 0)

        # can create project assigning the id
        project = models.Project.objects.create(
            id=first_id,
            revision='rev 1',
            name='a first project name',
        )

        # trying to update id
        project.id = second_id
        # it's trying to create a new project (not replacing the current one)
        with self.assertRaises(IntegrityError) as ie:
            project.save()

        self.assertIsNotNone(ie)
        self.assertIn('Key (name)=(a first project name) already exists.', str(ie.exception))

        # if we change the name we'll ended up with two projects
        project.name = 'a second project name'
        project.save()

        first_project = models.Project.objects.get(pk=first_id)
        self.assertIsNotNone(first_project)
        self.assertEqual(first_project.name, 'a first project name')

        second_project = models.Project.objects.get(pk=second_id)
        self.assertIsNotNone(second_project)
        self.assertEqual(second_project.name, 'a second project name')
