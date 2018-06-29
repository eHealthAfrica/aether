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

    def test_entity_filter(self):
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        # Get a list of all projects.
        projects = models.Project.objects.all()
        for project in projects:
            # Filter entities in all projects based on the project they are
            # associated with.
            entities = models.Entity.objects.filter(
                projectschema__project=project
            )
            # ...and retrieve all entity ids.
            expected = set([str(entity.id) for entity in entities])
            # Request a list of all entities, filtered by `project`.
            # This checks that EntityFilter.project exists and that
            # EntityFilter has been correctly configured.
            kwargs = {'project': str(project.id)}
            url = reverse(viewname='entity-list')
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            result = set([entity['id'] for entity in response['results']])
            self.assertEqual(expected, result)

    def test_submission_filter__by_instanceID(self):
        def gen_submission_payload():
            return {'meta': {'instanceID': str(uuid.uuid4())}}
        submission_field_values = {
            'payload': generators.CallableGenerator(gen_submission_payload)
        }
        generate_project(submission_field_values=submission_field_values)
        for submission in models.Submission.objects.all():
            instance_id = submission.payload['meta']['instanceID']
            kwargs = {'instanceID': instance_id}
            url = reverse(viewname='submission-list')
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            self.assertEqual(response['count'], 1)
            self.assertEqual(
                response['results'][0]['payload']['meta']['instanceID'],
                instance_id,
            )

    def test_submission_filter__by_project(self):
        # Generate projects.
        for _ in range(random.randint(10, 20)):
            generate_project()
        # Get a list of all projects.
        projects = models.Project.objects.all()
        for project in projects:
            # Filter submissions in all projects based on the project they are
            # associated with.
            submissions = models.Submission.objects.filter(
                mapping__project=project
            )
            # ...and retrieve all submission ids.
            expected = set([str(submission.id) for submission in submissions])
            # Request a list of all submissions, filtered by `project`.
            # This checks that SubmissionFilter.project exists and that
            # SubmissionFilter has been correctly configured.
            kwargs = {'project': str(project.id)}
            url = reverse(viewname='submission-list')
            response = json.loads(
                self.client.get(url, kwargs, format='json').content
            )
            # Check both sets of ids for equality.
            result = set([submission['id'] for submission in response['results']])
            self.assertEqual(expected, result)
