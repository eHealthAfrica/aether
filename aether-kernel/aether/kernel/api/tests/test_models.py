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
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TransactionTestCase

from aether.kernel.api import models

from . import EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA, EXAMPLE_SOURCE_DATA_ENTITY, EXAMPLE_MAPPING


class ModelsTests(TransactionTestCase):

    def test_models(self):

        project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
        )
        self.assertEquals(str(project), project.name)
        self.assertNotEqual(models.Project.objects.count(), 0)

        schema = models.Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision',
        )
        self.assertEquals(str(schema), schema.name)
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertIsNotNone(schema.definition_prettified)
        self.assertEqual(schema.schema_name, 'sample schema')

        schema.definition = EXAMPLE_SCHEMA
        schema.save()
        self.assertEqual(schema.schema_name, 'Person')

        projectschema = models.ProjectSchema.objects.create(
            name='sample project schema',
            project=project,
            schema=schema,
        )
        self.assertEquals(str(projectschema), projectschema.name)
        self.assertNotEqual(models.ProjectSchema.objects.count(), 0)

        mappingset = models.MappingSet.objects.create(
            revision='a sample revision',
            name='a sample mapping set',
            schema=EXAMPLE_SCHEMA,
            input=EXAMPLE_SOURCE_DATA,
            project=project,
        )
        self.assertEquals(str(mappingset), mappingset.name)
        self.assertNotEqual(models.MappingSet.objects.count(), 0)
        self.assertEquals(str(mappingset.project), str(project))
        self.assertIsNotNone(mappingset.input_prettified)
        self.assertIsNotNone(mappingset.schema_prettified)

        mapping = models.Mapping.objects.create(
            name='sample mapping',
            definition={'entities': {}, 'mapping': []},
            revision='a sample revision field',
            mappingset=mappingset,
        )
        self.assertEquals(str(mapping), mapping.name)
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertIsNotNone(mapping.definition_prettified)
        self.assertEqual(mapping.projectschemas.count(), 0, 'No entities in definition')

        mapping_definition = dict(EXAMPLE_MAPPING)
        mapping_definition['entities']['Person'] = str(projectschema.pk)
        mapping.definition = mapping_definition
        mapping.save()
        self.assertEqual(mapping.projectschemas.count(), 1)

        # check mapping definition validation
        mapping.definition = {'entities': {'a': str(uuid.uuid4())}}
        with self.assertRaises(IntegrityError) as err:
            mapping.save()
        message = str(err.exception)
        self.assertIn('is not valid under any of the given schemas', message)

        submission = models.Submission.objects.create(
            revision='a sample revision',
            payload=EXAMPLE_SOURCE_DATA,
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

        with self.assertRaises(IntegrityError) as err:
            models.Entity.objects.create(
                revision='a sample revision',
                payload=EXAMPLE_SOURCE_DATA,  # this is the submission payload without ID
                status='Publishable',
                projectschema=projectschema,
            )
        message = str(err.exception)
        self.assertIn('Extracted record did not conform to registered schema', message)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            projectschema=projectschema,
            mapping=mapping,
            submission=submission,
        )
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertIsNotNone(entity.payload_prettified)
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.name, f'{project.name}-{schema.schema_name}')
        self.assertEqual(entity.mapping_revision, mapping.revision,
                         'entity takes mapping revision if missing')

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
        self.assertIn('Submission, Mapping and Project Schema MUST belong to the same Project',
                      str(ie.exception))

        # it works without submission
        entity.submission = None
        entity.mapping = None
        entity.save()
        self.assertEqual(entity.project, project_2, 'entity inherits projectschema project')
        self.assertEqual(entity.name, f'{project_2.name}-{schema.schema_name}')

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
        entity.schema = None
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.name, entity.submission.name)

        entity.mapping = mapping
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits mapping project')

        entity.submission = None
        entity.projectschema = projectschema
        entity.save()
        self.assertEqual(entity.name, f'{project.name}-{schema.schema_name}')

        # try to build entity name with mapping entity entries
        projectschema_3 = models.ProjectSchema.objects.create(
            name='sample project schema 3',
            project=project,
            schema=schema,
        )

        self.assertEqual(mapping.projectschemas.count(), 1)
        mapping.definition = {
            'entities': {
                'None': str(projectschema_3.pk),
                'Some': str(entity.projectschema.pk),
            },
            'mapping': [],
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

    def test_model_deletion(self):

        project = models.Project.objects.create(
            name='project',
        )
        schema = models.Schema.objects.create(
            name='schema',
            definition=EXAMPLE_SCHEMA,
        )
        projectschema = models.ProjectSchema.objects.create(
            name='project schema',
            project=project,
            schema=schema,
        )
        entity = models.Entity.objects.create(
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            projectschema=projectschema,
        )

        entity_2 = models.Entity.objects.create(
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            schema=schema,
        )

        # delete the project will not delete the schema but one of the entities
        project.delete()

        self.assertTrue(models.Schema.objects.filter(pk=schema.pk).exists())
        self.assertFalse(models.Entity.objects.filter(pk=entity.pk).exists(), 'project CASCADE action')
        self.assertTrue(models.Entity.objects.filter(pk=entity_2.pk).exists(), 'Not linked to the project')
        self.assertFalse(models.Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(models.ProjectSchema.objects.filter(pk=projectschema.pk).exists())

        # repeat again but this time the schema is a passthrough schema

        project = models.Project.objects.create(
            name='project',
        )
        projectschema = models.ProjectSchema.objects.create(
            name='project schema',
            project=project,
            schema=schema,
        )
        schema.family = str(project.pk)
        schema.save()

        # delete the project will delete the schema and the entity
        project.delete()

        self.assertFalse(models.Schema.objects.filter(pk=schema.pk).exists())
        self.assertFalse(models.Entity.objects.filter(pk=entity_2.pk).exists(), 'schema CASCADE action')
        self.assertFalse(models.Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(models.ProjectSchema.objects.filter(pk=projectschema.pk).exists())

        # one more time but with more agents in the loop

        project = models.Project.objects.create(
            name='project',
        )
        schema = models.Schema.objects.create(
            name='schema',
            definition={},
            family=str(project.pk),
        )
        projectschema = models.ProjectSchema.objects.create(
            name='project schema',
            project=project,
            schema=schema,
        )
        models.ProjectSchema.objects.create(
            name='project schema 2',
            project=models.Project.objects.create(name='project 2'),
            schema=schema,
        )

        # delete the project will not delete the schema but clean the family content
        project.delete()

        self.assertTrue(models.Schema.objects.filter(pk=schema.pk).exists())
        schema.refresh_from_db()
        self.assertIsNone(schema.family)
