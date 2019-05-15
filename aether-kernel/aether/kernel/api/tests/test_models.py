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

from django.conf import settings
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TransactionTestCase, override_settings

from aether.kernel.api import models

from . import EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA, EXAMPLE_SOURCE_DATA_ENTITY, EXAMPLE_MAPPING


@override_settings(MULTITENANCY=False)
class ModelsTests(TransactionTestCase):

    def test_models(self):

        REALM = settings.DEFAULT_REALM

        project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
        )
        self.assertEqual(str(project), project.name)
        self.assertNotEqual(models.Project.objects.count(), 0)
        self.assertFalse(project.is_accessible(REALM))
        self.assertIsNone(project.get_realm())

        schema = models.Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision',
        )
        self.assertEqual(str(schema), schema.name)
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertIsNotNone(schema.definition_prettified)
        self.assertEqual(schema.schema_name, 'sample schema')

        schema.definition = EXAMPLE_SCHEMA
        schema.save()
        self.assertEqual(schema.schema_name, 'Person')

        schemadecorator = models.SchemaDecorator.objects.create(
            name='sample schema decorator',
            project=project,
            schema=schema,
        )
        self.assertEqual(str(schemadecorator), schemadecorator.name)
        self.assertNotEqual(models.SchemaDecorator.objects.count(), 0)
        self.assertIsNone(schemadecorator.revision)
        self.assertFalse(schemadecorator.is_accessible(REALM))
        self.assertIsNone(schemadecorator.get_realm())

        mappingset = models.MappingSet.objects.create(
            revision='a sample revision',
            name='a sample mapping set',
            schema=EXAMPLE_SCHEMA,
            input=EXAMPLE_SOURCE_DATA,
            project=project,
        )
        self.assertEqual(str(mappingset), mappingset.name)
        self.assertNotEqual(models.MappingSet.objects.count(), 0)
        self.assertIsNotNone(mappingset.input_prettified)
        self.assertIsNotNone(mappingset.schema_prettified)
        self.assertFalse(mappingset.is_accessible(REALM))
        self.assertIsNone(mappingset.get_realm())

        mapping = models.Mapping.objects.create(
            name='sample mapping',
            definition={'entities': {}, 'mapping': []},
            revision='a sample revision field',
            mappingset=mappingset,
        )
        self.assertEqual(str(mapping), mapping.name)
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertIsNotNone(mapping.definition_prettified)
        self.assertEqual(mapping.project, project)
        self.assertEqual(mapping.get_mt_instance(), project)
        self.assertEqual(mapping.schemadecorators.count(), 0, 'No entities in definition')
        self.assertFalse(mapping.is_accessible(REALM))
        self.assertIsNone(mapping.get_realm())

        mapping_definition = dict(EXAMPLE_MAPPING)
        mapping_definition['entities']['Person'] = str(schemadecorator.pk)
        mapping.definition = mapping_definition
        mapping.save()
        self.assertEqual(mapping.schemadecorators.count(), 1)

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
        self.assertEqual(str(submission), str(submission.id))
        self.assertEqual(submission.project, project, 'submission inherits mapping project')
        self.assertEqual(submission.get_mt_instance(), project)
        self.assertEqual(submission.name, 'a project name-a sample mapping set')
        self.assertFalse(submission.is_accessible(REALM))
        self.assertIsNone(submission.get_realm())

        attachment = models.Attachment.objects.create(
            submission=submission,
            attachment_file=SimpleUploadedFile('sample.txt', b'abc'),
        )
        self.assertEqual(str(attachment), attachment.name)
        self.assertEqual(attachment.name, 'sample.txt')
        self.assertEqual(attachment.md5sum, '900150983cd24fb0d6963f7d28e17f72')
        self.assertEqual(attachment.submission_revision, submission.revision)
        self.assertIsNone(attachment.revision)
        self.assertEqual(attachment.project, submission.project)
        self.assertEqual(attachment.attachment_file_url, attachment.attachment_file.url)
        self.assertFalse(attachment.is_accessible(REALM))
        self.assertIsNone(attachment.get_realm())

        attachment_2 = models.Attachment.objects.create(
            submission=submission,
            submission_revision='next revision',
            name='sample_2.txt',
            attachment_file=SimpleUploadedFile('sample_12345678.txt', b'abcd'),
        )
        self.assertEqual(str(attachment_2), attachment_2.name)
        self.assertEqual(attachment_2.name, 'sample_2.txt')
        self.assertEqual(attachment_2.md5sum, 'e2fc714c4727ee9395f324cd2e7f331f')
        self.assertEqual(attachment_2.submission_revision, 'next revision')
        self.assertNotEqual(attachment_2.submission_revision, submission.revision)

        with self.assertRaises(IntegrityError) as err:
            models.Entity.objects.create(
                revision='a sample revision',
                payload=EXAMPLE_SOURCE_DATA,  # this is the submission payload without ID
                status='Publishable',
                schemadecorator=schemadecorator,
            )
        message = str(err.exception)
        self.assertIn('Extracted record did not conform to registered schema', message)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            schemadecorator=schemadecorator,
            mapping=mapping,
            submission=submission,
        )
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertIsNotNone(entity.payload_prettified)
        self.assertEqual(str(entity), str(entity.id))
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.get_mt_instance(), project)
        self.assertEqual(entity.name, f'{project.name}-{schema.schema_name}')
        self.assertEqual(entity.mapping_revision, mapping.revision,
                         'entity takes mapping revision if missing')
        self.assertFalse(entity.is_accessible(REALM))
        self.assertIsNone(entity.get_realm())

        project_2 = models.Project.objects.create(
            revision='rev 1',
            name='a second project name',
        )
        schemadecorator_2 = models.SchemaDecorator.objects.create(
            name='sample second schema decorator',
            is_encrypted=False,
            project=project_2,
            schema=schema,
        )
        self.assertNotEqual(entity.submission.project, schemadecorator_2.project)
        entity.schemadecorator = schemadecorator_2
        with self.assertRaises(IntegrityError) as ie:
            entity.save()

        self.assertIsNotNone(ie)
        self.assertIn('Submission, Mapping and Schema Decorator MUST belong to the same Project',
                      str(ie.exception))

        # it works without submission
        entity.submission = None
        entity.mapping = None
        entity.save()
        self.assertEqual(entity.project, project_2, 'entity inherits schemadecorator project')
        self.assertEqual(entity.get_mt_instance(), project_2)
        self.assertEqual(entity.name, f'{project_2.name}-{schema.schema_name}')

        # keeps last project
        entity.schemadecorator = None
        entity.save()
        self.assertEqual(entity.project, project_2, 'entity keeps project')
        self.assertEqual(entity.name, entity.project.name)

        entity.project = None
        entity.save()
        self.assertEqual(entity.name, None)

        # till new submission or new schemadecorator is set
        entity.project = project_2  # this is going to be replaced
        entity.submission = submission
        entity.schemadecorator = None
        entity.schema = None
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits submission project')
        self.assertEqual(entity.name, entity.submission.name)

        entity.mapping = mapping
        entity.save()
        self.assertEqual(entity.project, project, 'entity inherits mapping project')

        entity.submission = None
        entity.schemadecorator = schemadecorator
        entity.save()
        self.assertEqual(entity.name, f'{project.name}-{schema.schema_name}')

        # try to build entity name with mapping entity entries
        schemadecorator_3 = models.SchemaDecorator.objects.create(
            name='sample schema decorator 3',
            project=project,
            schema=schema,
        )

        self.assertEqual(mapping.schemadecorators.count(), 1)
        mapping.definition = {
            'entities': {
                'None': str(schemadecorator_3.pk),
                'Some': str(entity.schemadecorator.pk),
            },
            'mapping': [],
        }
        mapping.save()
        self.assertEqual(mapping.schemadecorators.count(), 2)
        self.assertEqual(entity.name, f'{entity.project.name}-Some')

    def test_models_ids(self):

        first_id = uuid.uuid4()
        second_id = uuid.uuid4()
        self.assertNotEqual(first_id, second_id)
        self.assertFalse(models.Schema.objects.filter(pk=first_id).exists())
        self.assertFalse(models.Schema.objects.filter(pk=second_id).exists())

        # can create schema setting the id
        schema = models.Schema.objects.create(
            id=first_id,
            name='a first schema name',
            definition={},
        )

        # trying to update id
        schema.id = second_id
        # it's trying to create a new schema (not replacing the current one)
        with self.assertRaises(IntegrityError) as ie:
            schema.save()

        self.assertIsNotNone(ie)
        self.assertIn('Key (name)=(a first schema name) already exists.', str(ie.exception))

        # if we change the name we'll end up with two schemas
        schema.name = 'a second schema name'
        schema.save()

        self.assertTrue(models.Schema.objects.filter(pk=first_id).exists())
        first_schema = models.Schema.objects.get(pk=first_id)
        self.assertEqual(first_schema.name, 'a first schema name')

        self.assertTrue(models.Schema.objects.filter(pk=second_id).exists())
        second_project = models.Schema.objects.get(pk=second_id)
        self.assertEqual(second_project.name, 'a second schema name')

    def test_model_deletion(self):

        project = models.Project.objects.create(
            name='project',
        )
        schema = models.Schema.objects.create(
            name='schema',
            definition=EXAMPLE_SCHEMA,
        )
        schemadecorator = models.SchemaDecorator.objects.create(
            name='schema decorator',
            project=project,
            schema=schema,
        )
        entity = models.Entity.objects.create(
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            schemadecorator=schemadecorator,
        )
        entity_2 = models.Entity.objects.create(
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            schema=schema,
        )

        # delete the schema decorator will delete one of the entities
        schemadecorator.delete()

        self.assertFalse(models.Entity.objects.filter(pk=entity.pk).exists(), 'schema decorator CASCADE action')
        self.assertTrue(models.Entity.objects.filter(pk=entity_2.pk).exists(), 'Not linked to the schema decorator')

        # create again the deleted instances
        schemadecorator = models.SchemaDecorator.objects.create(
            name='schema decorator',
            project=project,
            schema=schema,
        )
        entity = models.Entity.objects.create(
            payload=EXAMPLE_SOURCE_DATA_ENTITY,
            status='Publishable',
            schemadecorator=schemadecorator,
        )

        # delete the project will not delete the schema but one of the entities
        project.delete()

        self.assertTrue(models.Schema.objects.filter(pk=schema.pk).exists())
        self.assertFalse(models.Entity.objects.filter(pk=entity.pk).exists(), 'project CASCADE action')
        self.assertTrue(models.Entity.objects.filter(pk=entity_2.pk).exists(), 'Not linked to the project')
        self.assertFalse(models.Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(models.SchemaDecorator.objects.filter(pk=schemadecorator.pk).exists())

        # repeat again but this time the schema is a passthrough schema

        project = models.Project.objects.create(
            name='project',
        )
        schemadecorator = models.SchemaDecorator.objects.create(
            name='schema decorator',
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
        self.assertFalse(models.SchemaDecorator.objects.filter(pk=schemadecorator.pk).exists())

        # one more time but with more agents in the loop

        project = models.Project.objects.create(
            name='project',
        )
        schema = models.Schema.objects.create(
            name='schema',
            definition={},
            family=str(project.pk),
        )
        schemadecorator = models.SchemaDecorator.objects.create(
            name='schema decorator',
            project=project,
            schema=schema,
        )
        models.SchemaDecorator.objects.create(
            name='schema decorator 2',
            project=models.Project.objects.create(name='project 2'),
            schema=schema,
        )

        # delete the project will not delete the schema but clean the family content
        project.delete()

        self.assertTrue(models.Schema.objects.filter(pk=schema.pk).exists())
        schema.refresh_from_db()
        self.assertIsNone(schema.family)

    def test_schema_decorator_topic_name(self):
        project = models.Project.objects.create(
            name='project',
        )
        schema = models.Schema.objects.create(
            name='schema',
            definition=EXAMPLE_SCHEMA,
        )
        schemadecorator = models.SchemaDecorator.objects.create(
            name='schema decorator',
            project=project,
            schema=schema,
        )
        self.assertEqual(schemadecorator.topic, {'name': 'schema decorator'})
