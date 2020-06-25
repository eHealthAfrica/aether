# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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

import random
import uuid

from locust import TaskSet, task

from settings import (
    AETHER_AUTH_HEADER,
    AETHER_KERNEL_URL,

    CREATE_PROJECT_PRIORITY,
    CREATE_SUBMISSION_PRIORITY,
    HEALTH_CHECK_PRIORITY,
    VIEW_PROJECTS_PRIORITY,
)


class KernelTaskSet(TaskSet):

    ###################################################
    # HELPERS
    ###################################################
    def health_check(self):
        self.client.get(
            name='/health',
            url=f'{AETHER_KERNEL_URL}/health',
        )

    def view_projects(self):
        self.client.get(
            name='/projects',
            headers=AETHER_AUTH_HEADER,
            url=f'{AETHER_KERNEL_URL}/projects.json',
        )

    def create_avro_schema(self):
        project_id = str(uuid.uuid4())
        avro_schema = {
            'name': f'simple-{project_id}',
            'type': 'record',
            'fields': [
                {
                'name': 'id',
                'type': 'string',
                },
                {
                'name': 'name',
                'type': 'string',
                }
            ],
        }

        self.client.request(
            name='/projects/avro-schemas',
            headers=AETHER_AUTH_HEADER,
            method='PATCH',
            url=f'{AETHER_KERNEL_URL}/projects/{project_id}/avro-schemas.json',
            json={
                'name': str(project_id),
                'avro_schemas': [{'definition': avro_schema}],
            },
        )

    def create_submission(self):
        # get list of mapping set ids
        response = self.client.get(
            url=f'{AETHER_KERNEL_URL}/mappingsets.json?fields=id&page_size=100',
            name='/mappingsets',
            headers=AETHER_AUTH_HEADER,
        )
        data = response.json()
        if data['count'] == 0:
            return

        # choose one random mapping set id
        results = data['results']
        size = len(results)
        _index = random.randint(0, size - 1)
        mappingset_id = results[_index]['id']

        submission_id = str(uuid.uuid4())
        submission_payload = {
            'id': submission_id,
            'name': f'Name {submission_id}',
        }

        self.client.request(
            name='/submissions',
            headers=AETHER_AUTH_HEADER,
            method='POST',
            url=f'{AETHER_KERNEL_URL}/submissions.json',
            json={
                'id': submission_id,
                'mappingset': mappingset_id,
                'payload': submission_payload,
            },
        )

    ###################################################
    # ON START
    ###################################################
    def on_start(self):
        self.client.get(
            name='/',
            headers=AETHER_AUTH_HEADER,
            url=f'{AETHER_KERNEL_URL}/',
        )

        # create initial project
        self.create_avro_schema()

    ###################################################
    # TASKS
    ###################################################
    @task(HEALTH_CHECK_PRIORITY)
    def task_health_check(self):
        self.health_check()

    @task(VIEW_PROJECTS_PRIORITY)
    def task_view_projects(self):
        self.view_projects()

    @task(CREATE_PROJECT_PRIORITY)
    def task_create_avro_schema(self):
        self.create_avro_schema()

    @task(CREATE_SUBMISSION_PRIORITY)
    def task_create_submission(self):
        self.create_submission()
