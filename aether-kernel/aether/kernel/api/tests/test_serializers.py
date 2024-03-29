# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import copy
import uuid

from django.test import RequestFactory, TestCase
from rest_framework.serializers import ValidationError

from aether.kernel.api import models, serializers

from . import EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA, EXAMPLE_SOURCE_DATA_ENTITY, EXAMPLE_MAPPING


class SerializersTests(TestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()
        self.request = RequestFactory().get('/')

    def test__serializers__create_and_update(self):

        project = serializers.ProjectSerializer(
            data={
                'name': 'a project name',
            },
            context={'request': self.request},
        )
        self.assertTrue(project.is_valid(), project.errors)
        project.save()

        project_1 = serializers.ProjectSerializer(
            data={
                'name': 'another project name',
            },
            context={'request': self.request},
        )
        self.assertTrue(project_1.is_valid(), project_1.errors)
        project_1.save()

        # check schema with definition validation
        schema = serializers.SchemaSerializer(
            data={
                'name': 'a schema name',
                'definition': {},
            },
            context={'request': self.request},
        )
        self.assertFalse(schema.is_valid(), schema.errors)
        self.assertIn('No "type" property', schema.errors['definition'][0])

        schema = serializers.SchemaSerializer(
            data={
                'name': 'a schema name',
                'definition': {
                    'type': 'record',
                },
            },
            context={'request': self.request},
        )
        self.assertFalse(schema.is_valid(), schema.errors)
        self.assertIn('Record schema requires a non-empty fields property.',
                      schema.errors['definition'][0])

        schema = serializers.SchemaSerializer(
            data={
                'name': 'a schema name',
                'definition': {
                    'name': 'Test',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'name',
                            'type': 'string',
                        }
                    ]
                },
            },
            context={'request': self.request},
        )
        self.assertFalse(schema.is_valid(), schema.errors)
        self.assertIn('A schema is required to have a field "id" of type "string"',
                      schema.errors['definition'][0])

        schema = serializers.SchemaSerializer(
            data={
                'name': 'a schema name',
                'definition': {
                    'name': 'Test',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'name',
                            'type': 'string',
                        }
                    ]
                },
            },
            context={'request': self.request},
        )
        self.assertFalse(schema.is_valid(), schema.errors)
        self.assertIn('A schema is required to have a field "id" of type "string"',
                      schema.errors['definition'][0])

        schema = serializers.SchemaSerializer(
            data={
                'name': 'a schema name',
                'definition': EXAMPLE_SCHEMA,
            },
            context={'request': self.request},
        )
        self.assertTrue(schema.is_valid(), schema.errors)
        schema.save()

        schemadecorator = serializers.SchemaDecoratorSerializer(
            data={
                'name': 'a schema decorator name',
                'project': project.data['id'],
                'schema': schema.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(schemadecorator.is_valid(), schemadecorator.errors)
        schemadecorator.save()

        schemadecorator_1 = serializers.SchemaDecoratorSerializer(
            data={
                'name': 'another schema decorator name',
                'project': project_1.data['id'],
                'schema': schema.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(schemadecorator_1.is_valid(), schemadecorator_1.errors)
        schemadecorator_1.save()

        mappingset = serializers.MappingSetSerializer(
            data={
                'name': 'a sample mapping set',
                'project': project.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(mappingset.is_valid(), mappingset.errors)
        mappingset.save()

        mappingset_1 = serializers.MappingSetSerializer(
            data={
                'name': 'another sample mapping set',
                'project': project_1.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(mappingset_1.is_valid(), mappingset_1.errors)
        mappingset_1.save()

        # check mapping with definition validation
        mapping = serializers.MappingSerializer(
            data={
                'name': 'a sample mapping',
                'definition': {
                    'entities': [],  # this must be a dict
                    'mapping': {},   # this must be a list
                },
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
            },
            context={'request': self.request},
        )
        self.assertFalse(mapping.is_valid(), mapping.errors)
        self.assertIn('is not valid under any of the given schemas',
                      mapping.errors['definition'][0])

        mapping_definition = copy.deepcopy(EXAMPLE_MAPPING)
        mapping_definition_1 = copy.deepcopy(EXAMPLE_MAPPING)
        mapping_definition['entities']['Person'] = schemadecorator.data['id']
        mapping_definition_1['entities']['Person'] = schemadecorator_1.data['id']
        mapping = serializers.MappingSerializer(
            data={
                'name': 'a sample mapping',
                'definition': mapping_definition,
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(mapping.is_valid(), mapping.errors)
        mapping.save()

        mapping_1 = serializers.MappingSerializer(
            data={
                'name': 'another sample mapping',
                'definition': mapping_definition_1,
                'mappingset': mappingset_1.data['id'],
                'project': project_1.data['id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(mapping_1.is_valid(), mapping_1.errors)
        mapping_1.save()

        # check the submission without mappingset
        submission = serializers.SubmissionSerializer(
            data={
                'project': project.data['id'],
                'payload': dict(EXAMPLE_SOURCE_DATA),
            },
            context={'request': self.request},
        )
        self.assertTrue(submission.is_valid(), submission.errors)

        with self.assertRaises(ValidationError) as ve_s:
            submission.save()
        self.assertIn('Mapping set must be provided on initial submission',
                      str(ve_s.exception))

        # check the submission with entity extraction errors
        submission = serializers.SubmissionSerializer(
            data={
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
                'payload': {},  # error
            },
            context={'request': self.request},
        )
        self.assertTrue(submission.is_valid(), submission.errors)

        # save the submission and check that no entities were created
        submission.save()
        submission_obj = models.Submission.objects.get(pk=submission.data['id'])
        self.assertEqual(submission_obj.entities.count(), 0)

        # update the submission
        submission_upd = serializers.SubmissionSerializer(
            submission_obj,
            data={
                'is_extracted': True,
                'payload': {},
            },
            context={'request': self.request},
        )
        self.assertTrue(submission_upd.is_valid(), submission_upd.errors)

        # save the submission
        submission_upd.save()

        # Create submission that fails validation
        submission_bad = serializers.SubmissionSerializer(
            data={
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
                'payload': EXAMPLE_SOURCE_DATA,
                'is_extracted': 'non-boolean'
            },
            context={'request': self.request},
        )
        self.assertFalse(submission_bad.is_valid(), submission_bad.errors)

        # check the submission without entity extraction errors
        submission = serializers.SubmissionSerializer(
            data={
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
                'payload': dict(EXAMPLE_SOURCE_DATA),
            },
            context={'request': self.request},
        )
        self.assertTrue(submission.is_valid(), submission.errors)

        # save the submission and check that the entities were created
        self.assertEqual(models.Entity.objects.count(), 0)
        submission.save()

        # check entity
        entity = serializers.EntitySerializer(
            data={
                'merge': 'overwrite',  # ignore in `create`
                'submission': submission.data['id'],
                'schemadecorator': schemadecorator.data['id'],
                'status': 'Pending Approval',
                'payload': dict(EXAMPLE_SOURCE_DATA),  # has no id
            },
            context={'request': self.request},
        )
        self.assertTrue(entity.is_valid(), entity.errors)

        with self.assertRaises(ValidationError) as ve_e:
            entity.save()
        self.assertIn('Extracted record did not conform to registered schema',
                      str(ve_e.exception))

        # create entity
        entity_2 = serializers.EntitySerializer(
            data={
                'submission': submission.data['id'],
                'schemadecorator': schemadecorator.data['id'],
                'mapping': mapping.data['id'],
                'status': 'Pending Approval',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_2.is_valid(), entity_2.errors)
        entity_2.save()

        # update entity
        entity_3 = serializers.EntitySerializer(
            models.Entity.objects.get(pk=entity_2.data['id']),
            data={
                **entity_2.data,
                'merge': 'last_write_wins',
                'status': 'Publishable',
                'payload': {'id': 1},  # wrong id type
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_3.is_valid(), entity_3.errors)

        with self.assertRaises(ValidationError) as ve_3:
            entity_3.save()
        self.assertIn('Extracted record did not conform to registered schema',
                      str(ve_3.exception))

        entity_4 = serializers.EntitySerializer(
            models.Entity.objects.get(pk=entity_2.data['id']),
            data={
                **entity_2.data,
                'merge': 'overwrite',
                'status': 'Publishable',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_4.is_valid(), entity_4.errors)
        entity_4.save()
        self.assertEqual(entity_2.data['id'], entity_4.data['id'])

        entity_5 = serializers.EntitySerializer(
            data={
                'submission': submission.data['id'],
                'mapping': mapping.data['id'],
                'schemadecorator': schemadecorator.data['id'],
                'status': 'Publishable',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_5.is_valid(), entity_5.errors)
        entity_5.save()
        self.assertEqual(entity_5.data['project'], submission.data['project'])

        entity_6 = serializers.EntitySerializer(
            data={
                'mapping': mapping.data['id'],
                'status': 'Pending Approval',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_6.is_valid(), entity_6.errors)
        with self.assertRaises(ValidationError) as ve_6:
            entity_6.save()
        self.assertIn('Schema Decorator MUST be provided with entities',
                      str(ve_6.exception))

        entity_7 = serializers.EntitySerializer(
            data={
                'status': 'Pending Approval',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_7.is_valid(), entity_7.errors)
        with self.assertRaises(ValidationError) as ve_7:
            entity_7.save()
        self.assertIn('Schema Decorator MUST be provided with entities',
                      str(ve_7.exception))
        entity_8 = serializers.EntitySerializer(
            data={
                'submission': submission.data['id'],
                'schemadecorator': schemadecorator.data['id'],
                'mapping': mapping_1.data['id'],
                'status': 'Pending Approval',
                'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            },
            context={'request': self.request},
        )
        self.assertTrue(entity_8.is_valid(), entity_8.errors)
        with self.assertRaises(ValidationError) as ve_8:
            entity_8.save()
        self.assertIn('Submission, Mapping and Schema Decorator MUST belong to the same Project',
                      str(ve_8.exception))

        # ----------------------------------------------------------------------
        # BULK OPERATIONS

        # ----------------------------------------------------------------------
        # SUBMISSIONS

        # create submissions
        submissions = [{
            'mappingset': 'wrong-id',
            'project': project.data['id'],
            'payload': EXAMPLE_SOURCE_DATA,
        }]
        bulk_submissions = serializers.SubmissionSerializer(
            data=submissions,
            many=True,
            context={'request': self.request},
        )
        self.assertFalse(bulk_submissions.is_valid(), bulk_submissions.errors)

        # missing mappingset
        submissions = [{
            'payload': EXAMPLE_SOURCE_DATA,
        }]
        bulk_submissions = serializers.SubmissionSerializer(
            data=submissions,
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(bulk_submissions.is_valid(), bulk_submissions.errors)
        with self.assertRaises(ValidationError) as ve_bs:
            bulk_submissions.save()
        self.assertIn('Mapping set must be provided on initial submission',
                      str(ve_bs.exception))

        # bulk too large
        big_submissions = [
            {
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
                'payload': EXAMPLE_SOURCE_DATA,
            }
            for __ in range(51)
        ]
        big_submissions = serializers.SubmissionSerializer(
            data=big_submissions,
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(big_submissions.is_valid(), big_submissions.errors)
        with self.assertRaises(ValidationError) as ve_bs:
            big_submissions.save()

        # good bulk
        submissions = [
            {
                'mappingset': mappingset.data['id'],
                'project': project.data['id'],
                'payload': EXAMPLE_SOURCE_DATA,
            }
            for __ in range(10)
        ]
        bulk_submissions = serializers.SubmissionSerializer(
            data=submissions,
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(bulk_submissions.is_valid(), bulk_submissions.errors)
        bulk_submissions.save()

        # bulk check update
        submission_instances = models.Submission.objects.filter(pk__in=[
            s['id'] for s in bulk_submissions.data
        ])
        bulk_submissions = serializers.SubmissionSerializer(
            submission_instances,
            data=[
                {'id': s.id, 'is_extracted': False}
                for s in submission_instances
            ],
            many=True,
            partial=True,
            context={'request': self.request},
        )
        self.assertTrue(bulk_submissions.is_valid(), bulk_submissions.errors)
        bulk_submissions.save()

        bulk_submissions = serializers.SubmissionSerializer(
            submission_instances,
            data=[
                {'id': s.id, 'mappingset': 'wrong-id'}
                for s in submission_instances
            ],
            many=True,
            partial=True,
            context={'request': self.request},
        )
        self.assertFalse(bulk_submissions.is_valid(), bulk_submissions.errors)

        # ----------------------------------------------------------------------
        # ENTITIES

        # bad bulk entity
        bad_bulk = serializers.EntitySerializer(
            data=[{
                'schemadecorator': schemadecorator.data['id'],
                'status': 'Pending Approval',
                'payload': {'bad': 'entity'}
            }],
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(bad_bulk.is_valid(), bad_bulk.errors)
        with self.assertRaises(ValidationError) as ve_be:
            bad_bulk.save()
        self.assertIn('Extracted record did not conform to registered schema',
                      str(ve_be.exception))

        # bulk to large
        payloads = [EXAMPLE_SOURCE_DATA_ENTITY for __ in range(51)]
        for pl in payloads:
            pl.update({'id': str(uuid.uuid4())})
        data = [
            {
                'schemadecorator': schemadecorator.data['id'],
                'status': 'Pending Approval',
                'payload': pl
            } for pl in payloads
        ]
        # submit at once
        bad_bulk = serializers.EntitySerializer(
            data=data,
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(bad_bulk.is_valid(), bad_bulk.errors)
        with self.assertRaises(ValidationError) as ve_be:
            bad_bulk.save()

        # good bulk
        # make objects
        payloads = [EXAMPLE_SOURCE_DATA_ENTITY for __ in range(6)]
        for pl in payloads:
            pl.update({'id': str(uuid.uuid4())})
        data = [
            {
                'schemadecorator': schemadecorator.data['id'],
                'status': 'Pending Approval',
                'payload': pl
            } for pl in payloads
        ]
        # submit at once
        bulk_entities = serializers.EntitySerializer(
            data=data,
            many=True,
            context={'request': self.request},
        )
        self.assertTrue(bulk_entities.is_valid(), bulk_entities.errors)
        bulk_entities.save()
