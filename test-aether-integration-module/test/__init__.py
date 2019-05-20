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

import os
from time import sleep

import pytest
import requests

# Register Test Project and provide access to artifacts through client test fixtures
from aether.client.test_fixtures import client, project, schemas, schemadecorators, mapping, mappingset  # noqa
from aether.client import fixtures  # noqa

from .consumer import get_consumer, read


FORMS_TO_SUBMIT = 10
SEED_ENTITIES = 10 * 7  # 7 Vaccines in each report


SEED_TYPE = 'CurrentStock'
REALM = os.environ['TEST_REALM']
KAFKA_SEED_TYPE = f'{REALM}.{SEED_TYPE}'

PRODUCER_CREDS = [
    os.environ['PRODUCER_ADMIN_USER'],
    os.environ['PRODUCER_ADMIN_PW']
]


@pytest.fixture(scope='function')
def producer_topics():
    max_retry = 10
    for x in range(max_retry):
        try:
            status = producer_request('status')
            kafka = status.get('kafka_container_accessible')
            if not kafka:
                raise ValueError('Kafka not connected yet')
            topics = producer_request('topics')
            return topics
        except Exception:
            sleep(1)


@pytest.fixture(scope='function')
def wait_for_producer_status():
    max_retry = 30
    failure_mode = None
    for x in range(max_retry):
        try:
            status = producer_request('status')
            if not status:
                raise ValueError('No status response from producer')
            kafka = status.get('kafka_container_accessible')
            if not kafka:
                raise ValueError('Kafka not connected yet')
            person = status.get('topics', {}).get(KAFKA_SEED_TYPE, {})
            ok_count = person.get('last_changeset_status', {}).get('succeeded')
            if ok_count:
                sleep(5)
                return ok_count
            else:
                raise ValueError('Last changeset status has no successes. Not producing')
        except Exception as err:
            failure_mode = str(err)
            sleep(1)

    raise TimeoutError(f'Producer not ready before {max_retry}s timeout. Reason: {failure_mode}')


@pytest.fixture(scope='function')  # noqa
def entities(client, schemadecorators):  # noqa: F811
    entities = {}
    for sd in schemadecorators:
        name = sd['name']
        sd_id = sd.id
        entities[name] = [i for i in client.entities.paginated(
            'list', schemadecorator=sd_id)]
    return entities


@pytest.fixture(scope='function')
def generate_entities(client, mappingset):  # noqa: F811
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


@pytest.fixture(scope='function')
def read_people():
    consumer = get_consumer(KAFKA_SEED_TYPE)
    messages = read(consumer, start='FIRST', verbose=False, timeout_ms=500)
    consumer.close()  # leaving consumers open can slow down zookeeper, try to stay tidy
    return messages


# Producer convenience functions


def producer_request(endpoint, expect_json=True):
    auth = requests.auth.HTTPBasicAuth(*PRODUCER_CREDS)
    url = '{base}/{endpoint}'.format(
        base=os.environ['PRODUCER_URL'],
        endpoint=endpoint)
    try:
        res = requests.get(url, auth=auth)
        if expect_json:
            return res.json()
        else:
            return res.text
    except Exception as err:
        print(err)
        sleep(1)


def topic_status(topic):
    status = producer_request('status')
    return status['topics'][topic]


def producer_topic_count(topic):
    status = producer_request('topics')
    return status[topic]['count']


def producer_control_topic(topic, operation):
    endpoint = f'{operation}?topic={topic}'
    return producer_request(endpoint, False)
