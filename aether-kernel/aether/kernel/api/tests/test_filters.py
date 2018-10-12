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

import json
import random
import uuid

from autofixture import generators
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from aether.kernel.api import models
from aether.kernel.api.tests.utils.generators import generate_project


class TestFilters(TestCase):

    def setUp(self):
        username = 'user'
        email = 'user@example.com'
        password = 'password'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def test_project_filter__by_schema(self):
        url = reverse(viewname='project-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Project.objects.count()
        # Get a list of all schemas.
        for schema in models.Schema.objects.all():
            # Request a list of all projects, filtered by `schema`.
            # This checks that ProjectFilter.schema exists and that
            # ProjectFilter has been correctly configured.
            expected = set([str(e.project.id) for e in schema.projectschemas.all()])

            # by id
            kwargs = {'schema': str(schema.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'schema': schema.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_schema_filter__by_project(self):
        url = reverse(viewname='schema-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Schema.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all schemas, filtered by `project`.
            # This checks that SchemaFilter.project exists and that
            # SchemaFilter has been correctly configured.
            expected = set([str(e.schema.id) for e in project.projectschemas.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_project(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Entity.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all entities, filtered by `project`.
            # This checks that EntityFilter.project exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in project.entities.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_mapping(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Entity.objects.count()
        # Get a list of all mappings.
        for mapping in models.Mapping.objects.all():
            # Request a list of all entities, filtered by `mapping`.
            # This checks that EntityFilter.mapping exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in mapping.entities.all()])

            # by id
            kwargs = {'mapping': str(mapping.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'mapping': mapping.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_schema(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Entity.objects.count()
        # Get a list of all schemas.
        for schema in models.Schema.objects.all():
            # Request a list of all entities, filtered by `schema`.
            # This checks that EntityFilter.schema exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in models.Entity.objects.filter(projectschema__schema=schema)])

            # by id
            kwargs = {'schema': str(schema.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'schema': schema.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_submission(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        page_size = models.Entity.objects.count()
        # Get a list of all submissions.
        for submission in models.Submission.objects.all():
            # Request a list of all entities, filtered by `submission`.
            # This checks that EntityFilter.submission exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in submission.entities.all()])

            kwargs = {'submission': str(submission.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_submission_filter__by_instanceID(self):
        def gen_submission_payload():
            return {'meta': {'instanceID': str(uuid.uuid4())}}
        submission_field_values = {
            'payload': generators.CallableGenerator(gen_submission_payload)
        }
        generate_project(submission_field_values=submission_field_values)
        url = reverse(viewname='submission-list')
        for submission in models.Submission.objects.all():
            instance_id = submission.payload['meta']['instanceID']
            kwargs = {'instanceID': instance_id}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            self.assertEqual(response['count'], 1)
            self.assertEqual(
                response['results'][0]['payload']['meta']['instanceID'],
                instance_id,
            )

    def test_submission_filter__by_project(self):
        url = reverse(viewname='submission-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Submission.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all submissions, filtered by `project`.
            # This checks that SubmissionFilter.project exists and that
            # SubmissionFilter has been correctly configured.
            expected = set([str(s.id) for s in project.submissions.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_submission_filter__by_mappingset(self):
        url = reverse(viewname='submission-list')
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        page_size = models.Submission.objects.count()
        # Get a list of all mapping sets.
        for mappingset in models.MappingSet.objects.all():
            # Request a list of all submissions, filtered by `mappingset`.
            # This checks that SubmissionFilter.mappingset exists and that
            # SubmissionFilter has been correctly configured.
            expected = set([str(e.id) for e in mappingset.submissions.all()])

            # by id
            kwargs = {'mappingset': str(mappingset.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'mappingset': mappingset.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_mapping_filter__by_mappingset(self):
        url = reverse(viewname='mapping-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        page_size = models.Mapping.objects.count()
        # Get a list of all mapping sets.
        for mappingset in models.MappingSet.objects.all():
            expected = set([str(e.id) for e in mappingset.mappings.all()])
            # by id
            kwargs = {'mappingset': str(mappingset.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'mappingset': mappingset.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_mapping_filter__by_projectschema(self):
        url = reverse(viewname='mapping-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        page_size = models.Mapping.objects.count()
        # Get a list of all project schemas.
        for projectschema in models.ProjectSchema.objects.all():
            expected = set([str(e.id) for e in projectschema.mappings.all()])
            # by id
            kwargs = {'projectschema': str(projectschema.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'projectschema': projectschema.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_mappingset_filter__by_project(self):
        url = reverse(viewname='mappingset-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        page_size = models.MappingSet.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            expected = set([str(s.id) for s in project.mappingsets.all()])
            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': page_size}
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_submission_filter__payload(self):
        url = reverse(viewname='submission-list')
        filters = [
            {'payload__a': '1'},
            {'payload__a__b': '"abcde"'},
            {'payload__a__b__c': '[1,2,3]'},
        ]
        payloads = [
            {'a': 1},
            {'a': {'b': 'abcde'}},
            {'a': {'b': {'c': [1,2,3]}}}
        ]
        gen_payload = generators.ChoicesGenerator(values=payloads)
        generate_project(submission_field_values={'payload': gen_payload})
        filtered_submissions_count = 0
        for kwargs, payload in zip(filters, payloads):
            response = self.client.get(url, kwargs, format='json')
            submissions = json.loads(response.content)['results']
            for submission in submissions:
                self.assertEqual(submission['payload'], payload)
                filtered_submissions_count += 1
        self.assertEqual(
            len(models.Submission.objects.all()),
            filtered_submissions_count,
        )
