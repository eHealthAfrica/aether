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

from time import sleep

import pytest
import requests

# Register Test Project and provide access to artifacts through client test fixtures
from aether.client.test_fixtures import client, project, schemas, projectschemas, mapping, mappingset  # noqa
from aether.client import fixtures  # noqa

from .consumer import get_consumer, read

FORMS_TO_SUBMIT = 10
SEED_ENTITIES = 10 * 7  # 7 Vaccines in each report
SEED_TYPE = "CurrentStock"


@pytest.fixture(scope="function")
def producer_status():
    max_retry = 30
    url = "http://producer-test:9005/status"
    for x in range(max_retry):
        try:
            status = requests.get(url).json()
            kafka = status.get('kafka_container_accessible')
            if not kafka:
                raise ValueError('Kafka not connected yet')
            person = status.get('topics', {}).get(SEED_TYPE, {})
            ok_count = person.get('last_changeset_status', {}).get('succeeded')
            if ok_count:
                sleep(10)
                return ok_count
            else:
                sleep(1)
        except Exception as err:
            print(err)
            sleep(1)


@pytest.fixture(scope="function")  # noqa
def entities(client, projectschemas):
    entities = {}
    for ps in projectschemas:
        name = ps["name"]
        ps_id = ps.id
        entities[name] = [i for i in client.entities.paginated(
            'list', projectschema=ps_id)]
    return entities


@pytest.fixture(scope="function")  # noqa
def generate_entities(client, mappingset):
    payloads = iter(fixtures.get_submission_payloads())
    entities = []
    for i in range(FORMS_TO_SUBMIT):
        Submission = client.get_model('Submission')
        submission = Submission(
            payload=next(payloads),
            mappingset=mappingset.id
        )
        instance = client.submissions.create(data=submission)
        for entity in client.entities.paginated('list', submission=instance.id):
            entities.append(entity)
    return entities


@pytest.fixture(scope="function")
def read_people():
    consumer = get_consumer(SEED_TYPE)
    messages = read(consumer, start="FIRST", verbose=False, timeout_ms=500)
    consumer.close()  # leaving consumers open can slow down zookeeper, try to stay tidy
    return messages
