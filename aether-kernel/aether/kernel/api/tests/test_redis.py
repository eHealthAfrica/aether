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

import uuid
from django.test import TransactionTestCase
from django.conf import settings
from aether.python.redis.task import TaskHelper

from ..models import Project, Schema, SchemaDecorator, Mapping, MappingSet, Submission
from ..redis import (
    get_redis_project_artefacts,
    are_all_items_in_object,
    in_same_project_and_cache
)
from ..constants import PROJECT_ARTEFACT_CACHE

REDIS_TASK = TaskHelper(settings)


class RedisTests(TransactionTestCase):

    def test_get_redis_project_artefacts(self):
        project_id = uuid.uuid4()
        project = Project.objects.create(
            id=project_id,
            revision='rev 1',
            name='a project name - redis',
        )
        artefacts = get_redis_project_artefacts(project)
        self.assertEqual(str(project_id), artefacts['data']['project'])
        self.assertIn('submissions', artefacts['data'])

        REDIS_TASK.remove(_id=project_id, type=PROJECT_ARTEFACT_CACHE, tenant=settings.DEFAULT_REALM)
        artefacts = get_redis_project_artefacts(project)
        self.assertIsNone(artefacts)

    def test_are_all_items_in_object(self):
        _object = {
            'a': ['123', '12', '1'],
            'b': ['abc', 'ab', 'c']
        }
        _items = {
            'a': '12',
            'b': 'c'
        }
        _result = are_all_items_in_object(_object, _items)
        self.assertTrue(_result)

        _wrong_items = {
            'a': '1234',
            'b': 'abc'
        }
        _result = are_all_items_in_object(_object, _wrong_items)
        self.assertFalse(_result)

        _ext_items = {
            'a': '123',
            'b': 'abc',
            'c': '1234'
        }
        _result = are_all_items_in_object(_object, _ext_items)
        self.assertTrue(_result)

    def test_in_same_project_and_cache(self):
        project_id = uuid.uuid4()
        project = Project.objects.create(
            id=project_id,
            revision='rev 1',
            name='another project name - redis',
        )
        schema = Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision',
        )
        schemadecorator = SchemaDecorator.objects.create(
            name='sample schema decorator',
            project=project,
            schema=schema,
        )
        mappingset = MappingSet.objects.create(
            schema={},
            input={},
            project=project,
            name='mappingset1',
        )
        mapping = Mapping.objects.create(
            mappingset=mappingset,
            definition={'entities': {}, 'mapping': []},
            name='mapping1'
        )

        artefacts = {
            'schema_decorators': str(schemadecorator.pk)
        }
        _result = in_same_project_and_cache(artefacts, project)
        self.assertTrue(_result)

        REDIS_TASK.remove(_id=project_id, type=PROJECT_ARTEFACT_CACHE, tenant=settings.DEFAULT_REALM)

        _result = in_same_project_and_cache(artefacts, project)
        self.assertTrue(_result)

        for i in range(5):
            submission = Submission.objects.create(
                payload={},
                mappingset=mappingset,
                project=project
            )
            artefacts = {
                'schema_decorators': str(schemadecorator.pk),
                'submissions': str(submission.pk),
                'mappings': str(mapping.pk),
            }
            _result = in_same_project_and_cache(artefacts, project)
            self.assertTrue(_result)

        artefacts = {
            'schema_decorators': str(schemadecorator.pk),
            'submissions': 'wrong-submission-id',
            'mappings': str(mapping.pk),
        }
        _result = in_same_project_and_cache(artefacts, project)
        self.assertFalse(_result)

        redis_mock = {
            'schema_decorators': [str(schemadecorator.pk), ],
            'submissions': [str(submission.pk), ],
            'mappings': [str(mapping.pk), ],
        }

        artefacts = {
            'schema_decorators': str(schemadecorator.pk),
            'submissions': str(submission.pk),
            'mappings': str(mapping.pk),
        }

        _result = are_all_items_in_object(redis_mock, artefacts, str(submission.project.pk))
        self.assertTrue(_result)

        _result = are_all_items_in_object(redis_mock, artefacts, 'different-project-id')
        self.assertFalse(_result)

        artefacts = {
            'schema_decorators': str(schemadecorator.pk),
            'submissions': 'extracted-submission-id',
            'mappings': str(mapping.pk),
        }

        redis_mock = {
            'schema_decorators': [str(schemadecorator.pk), ],
            'submissions': [str(submission.pk), 'extracted-submission-id'],
            'mappings': [str(mapping.pk), ],
        }

        _result = are_all_items_in_object(redis_mock, artefacts)
        self.assertTrue(_result)

        artefacts = {
            'schema_decorators': str(schemadecorator.pk),
            'submissions': 'extracted-submission-missing',
            'mappings': str(mapping.pk),
        }

        _result = are_all_items_in_object(redis_mock, artefacts)
        self.assertFalse(_result)
