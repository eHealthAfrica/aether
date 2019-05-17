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

from . import *


####################################################################################
#  Create Schemas -> Entities -> Produce -> Check in Kafka for result
####################################################################################


def test_1_check_fixtures(project, schemas, schemadecorators, mapping, mappingset):
    for asset in [project, mapping, mappingset]:
        assert(asset.id is not None)
    for sch in schemas:
        assert(sch.id is not None)
    for sd in schemadecorators:
        assert(sd.id is not None)


def test_2_generate_entities(generate_entities):
    assert(len(generate_entities) == SEED_ENTITIES)


def test_3_check_updated_count(entities):
    assert(len(entities.get(SEED_TYPE)) >= SEED_ENTITIES)


def test_4_check_producer_status(wait_for_producer_status):
    assert(wait_for_producer_status is not None)


def test_5_check_producer_topics(producer_topics):
    assert(SEED_TYPE in producer_topics.keys())
    assert(int(producer_topics[SEED_TYPE]['count']) is SEED_ENTITIES)


def test_6_check_stream_entities(read_people, entities):
    kernel_messages = [msg.payload.get('id') for msg in entities.get(SEED_TYPE)]
    kafka_messages = [msg['id'] for msg in read_people]
    failed = []
    for _id in kernel_messages:
        if _id not in kafka_messages:
            failed.append(_id)
    assert(len(failed) == 0)
    assert(len(kernel_messages) == len(kafka_messages))
    assert(producer_topic_count(SEED_TYPE) == len(kafka_messages))


def test_7_control_topic():
    producer_control_topic(SEED_TYPE, 'pause')
    sleep(.5)
    op = topic_status(SEED_TYPE)['operating_status']
    assert(op == 'TopicStatus.PAUSED')
    producer_control_topic(SEED_TYPE, 'resume')
    sleep(.5)
    op = topic_status(SEED_TYPE)['operating_status']
    assert(op == 'TopicStatus.NORMAL')
    producer_control_topic(SEED_TYPE, 'rebuild')
    sleep(.5)
    for x in range(120):
        op = topic_status(SEED_TYPE)['operating_status']
        if op != 'TopicStatus.REBUILDING':
            return
        sleep(1)
    assert(False), 'Topic Deletion Timed out.'
