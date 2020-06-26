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

from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from aether.kernel.api import models
from aether.kernel.api.entity_extractor import parse_delta, run_entity_extraction

from . import EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA


@override_settings(MULTITENANCY=False)
class EntityExtractorTest(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        # Set up test model instances:
        self.project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
        )

        self.schema = models.Schema.objects.create(
            name='schema1',
            type='eha.test.schemas',
            family='Person',
            definition=EXAMPLE_SCHEMA,
        )

        self.schemadecorator = models.SchemaDecorator.objects.create(
            name='a schema decorator name',
            project=self.project,
            schema=self.schema,
        )
        # update the fake value with a real one
        mapping_definition = dict(EXAMPLE_MAPPING)
        mapping_definition['entities']['Person'] = str(self.schemadecorator.pk)

        self.mappingset = models.MappingSet.objects.create(
            name='a sample mapping set',
            input={},
            schema={},
            project=self.project,
        )

        self.mapping = models.Mapping.objects.create(
            name='mapping1',
            definition=mapping_definition,
            mappingset=self.mappingset,
        )

        self.submission = models.Submission.objects.create(
            payload=EXAMPLE_SOURCE_DATA,
            mappingset=self.mappingset,
            project=self.project,
        )

    def tearDown(self):
        self.project.delete()
        self.client.logout()

    def test_parse_delta_delta(self):
        fixed_now = now()

        with mock.patch('aether.kernel.api.entity_extractor.now', return_value=fixed_now):
            self.assertEqual(parse_delta('3d'), fixed_now - timedelta(days=3))
            self.assertEqual(parse_delta('3days'), fixed_now - timedelta(days=3))
            self.assertEqual(parse_delta('days3'), fixed_now - timedelta(days=3))

            self.assertEqual(parse_delta('2w'), fixed_now - timedelta(weeks=2))
            self.assertEqual(parse_delta('2weeks'), fixed_now - timedelta(weeks=2))
            self.assertEqual(parse_delta('weeks2'), fixed_now - timedelta(weeks=2))

            self.assertEqual(parse_delta('10m'), fixed_now - timedelta(minutes=10))
            self.assertEqual(parse_delta('10minutes'), fixed_now - timedelta(minutes=10))
            self.assertEqual(parse_delta('minutes10'), fixed_now - timedelta(minutes=10))

            self.assertEqual(parse_delta('5h'), fixed_now - timedelta(hours=5))
            self.assertEqual(parse_delta('5hours'), fixed_now - timedelta(hours=5))
            self.assertEqual(parse_delta('hours5'), fixed_now - timedelta(hours=5))

            self.assertEqual(parse_delta(None), fixed_now - timedelta(days=1))
            self.assertEqual(parse_delta('no-value'), fixed_now - timedelta(days=1))
            self.assertEqual(parse_delta('12345'), fixed_now - timedelta(days=1))
            self.assertEqual(parse_delta('12years'), fixed_now - timedelta(days=1))

    def test_project__extract__endpoint(self):
        def my_side_effect(submission, overwrite):
            # let the submission 2 pass but raise an error for self.submission
            if submission == self.submission:
                raise Exception('oops')
            else:
                run_entity_extraction(submission, overwrite)

        self.assertEqual(reverse('project-extract', kwargs={'pk': 1}),
                         '/projects/1/extract/')
        url = reverse('project-extract', kwargs={'pk': self.project.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 405, 'only PATCH')

        # create a second submission
        submission_2 = models.Submission.objects.create(
            payload=EXAMPLE_SOURCE_DATA,
            mappingset=self.mappingset,
            project=self.project,
        )
        models.Entity.objects.all().delete()  # remove all entities

        self.assertEqual(self.project.submissions.count(), 2)
        self.assertEqual(self.project.entities.count(), 0)
        self.submission.is_extracted = False
        self.submission.save()

        with mock.patch('aether.kernel.api.entity_extractor.run_entity_extraction',
                        side_effect=my_side_effect) as mock_fn:
            response = self.client.patch(url)

        mock_fn.assert_has_calls([
            mock.call(self.submission, False),
            mock.call(submission_2, False),
        ])

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.project.entities.count(), 0)
        self.assertNotEqual(submission_2.entities.count(), 0)
        self.assertEqual(self.submission.entities.count(), 0)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.payload['aether_errors'], ['oops'])

    def test_mappingset__extract__endpoint(self):
        def my_side_effect(submission, overwrite):
            # let the submission 2 pass but raise an error for self.submission
            if submission == self.submission:
                raise Exception('oops')
            else:
                run_entity_extraction(submission, overwrite)

        self.assertEqual(reverse('mappingset-extract', kwargs={'pk': 1}),
                         '/mappingsets/1/extract/')
        url = reverse('mappingset-extract', kwargs={'pk': self.mappingset.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 405, 'only PATCH')

        # create more than 100 submissions
        for _ in range(100):
            models.Submission.objects.create(
                payload=EXAMPLE_SOURCE_DATA,
                mappingset=self.mappingset,
                project=self.project,
            )
        self.assertEqual(self.mappingset.submissions.count(), 101)

        # send to redis the submissions older than one day
        with mock.patch('aether.kernel.api.entity_extractor.send_model_item_to_redis') as mock_fn_1:
            response = self.client.patch(url + '?&delta=1d')

        mock_fn_1.assert_not_called()  # the submissions are not older than 1 day
        self.assertEqual(response.status_code, 200)

        # force extraction and send to redis
        with mock.patch('aether.kernel.api.entity_extractor.send_model_item_to_redis') as mock_fn_2:
            response = self.client.patch(url + '?overwrite=t')

        mock_fn_2.assert_called()
        self.assertEqual(response.status_code, 200)

    def test_submission__extract__endpoint(self):
        self.assertEqual(reverse('submission-extract', kwargs={'pk': 1}),
                         '/submissions/1/extract/')
        url = reverse('submission-extract', kwargs={'pk': self.submission.pk})

        self.assertEqual(self.submission.entities.count(), 0)
        self.assertNotIn('aether_errors', self.submission.payload)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 405, 'only PATCH')

        with mock.patch('aether.kernel.api.entity_extractor.extract_create_entities',
                        side_effect=Exception('oops')) as mock_fn:
            response = self.client.patch(url)

        mock_fn.assert_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submission.entities.count(), 0)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.payload['aether_errors'], ['oops'])

        response = self.client.patch(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.submission.entities.count(), 0)
