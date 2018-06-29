#!/usr/bin/env python

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

import io
import json
import mock
import pytest
from time import sleep
from copy import deepcopy
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from spavro.datafile import DataFileWriter
from spavro.io import DatumWriter
from spavro.schema import parse as ParseSchema

from aet.consumer import KafkaConsumer
from .assets.schemas import test_schemas

kafka_server = "kafka-test:29092"
kafka_connection_retry = 10
kafka_connection_retry_wait = 6
# increasing topic_size may cause poll to be unable to get all the messages in one call.
# needs to be even an if > 100 a multiple of 100.
topic_size = 500


def send_messages(producer, name, schema, messages):
    bytes_writer = io.BytesIO()
    writer = DataFileWriter(bytes_writer, DatumWriter(), schema, codec='deflate')
    for msg in messages:
        writer.append(msg)
    writer.flush()
    raw_bytes = bytes_writer.getvalue()
    writer.close()
    future = producer.send(name, key=str(msg.get("id")), value=raw_bytes)
    # block until it actually sends.
    record_metadata = future.get(timeout=100)
    if not record_metadata:
        pass  # we may want to check the metadata in the future
    producer.flush()


def write_to_topic(schema_name):
    producer = None
    for x in range(kafka_connection_retry):
        try:
            producer = KafkaProducer(bootstrap_servers=kafka_server,
                                     acks=1, key_serializer=str.encode)
            break
        except NoBrokersAvailable:
            sleep(kafka_connection_retry_wait)
    if not producer:
        raise NoBrokersAvailable("Could not attach to kafka after %s seconds. Check configuration" %
                                 (kafka_connection_retry * kafka_connection_retry_wait))
    assets = test_schemas.get(schema_name)
    schema = assets.get("schema")
    schema = ParseSchema(json.dumps(schema, indent=2))
    mocker = assets.get("mocker")
    messages = []
    # the parcel gets large if you stick too many messages in it.
    # 100 serialzed together effectively minimizes the impact of passing the schema.
    if topic_size > 100:
        for x in range(0, topic_size, 100):
            batch = mocker(count=100)
            messages.extend(batch)
            send_messages(producer, schema_name, schema, batch)
    else:
        messages = mocker(count=topic_size)
        send_messages(producer, schema_name, schema, messages)
    producer.close()
    return messages


@pytest.mark.integration
@pytest.fixture(scope="function")
def default_consumer_args():
    return deepcopy({
        "aether_masking_schema_annotation": "aetherMaskingLevel",
        "aether_emit_flag_field_path": "$.publish",
        "aether_emit_flag_values": [True, False],
        "aether_masking_schema_levels": [0, 1, 2, 3, 4, 5],
        "aether_masking_schema_emit_level": 0,
        "bootstrap_servers": kafka_server,
        "heartbeat_interval_ms": 2500,
        "session_timeout_ms": 18000,
        "request_timeout_ms": 20000,
        "auto_offset_reset": 'latest',
        "consumer_timeout_ms": 17000
    })


@pytest.mark.integration
@pytest.fixture(scope="session")
def messages_test_boolean_pass():
    messages = write_to_topic("TestBooleanPass")
    return messages


@pytest.mark.integration
@pytest.fixture(scope="session")
def messages_test_enum_pass():
    messages = write_to_topic("TestEnumPass")
    return messages


@pytest.mark.integration
@pytest.fixture(scope="session")
def messages_test_secret_pass():
    messages = write_to_topic("TestTopSecret")
    return messages


@pytest.mark.unit
@pytest.fixture(scope="session")
def sample_schema():
    assets = test_schemas.get("TestBooleanPass")
    return assets.get("schema")


@pytest.mark.unit
@pytest.fixture(scope="function")
def sample_message():
    assets = test_schemas.get("TestBooleanPass")
    mocker = assets.get("mocker")
    yield mocker()[0]


@pytest.mark.unit
@pytest.fixture(scope="session")
def sample_schema_top_secret():
    assets = test_schemas.get("TestTopSecret")
    return assets.get("schema")


@pytest.mark.unit
@pytest.fixture(scope="function")
def sample_message_top_secret():
    assets = test_schemas.get("TestTopSecret")
    mocker = assets.get("mocker")
    yield mocker()[0]


@pytest.mark.unit
@pytest.fixture(scope="function")
def offline_consumer():
    consumer = None

    def set_config(self, new_configs):
        self.config = new_configs

    def add_config(self, pairs):
        for k, v in pairs.items():
            self.config[k] = v
    # Mock up a usable KafkaConsumer that doesn't use Kafka...
    with mock.patch('aether.consumer.VanillaConsumer.__init__') as MKafka:
        MKafka.return_value = None  # we need to ignore the call to super in __init__
        consumer = KafkaConsumer()
    consumer._set_config = set_config.__get__(consumer)
    consumer._add_config = add_config.__get__(consumer)
    # somehow the ADDITIONAL_CONFIG changes if you pass it directly.
    # Leave this deepcopy
    consumer._set_config(deepcopy(KafkaConsumer.ADDITIONAL_CONFIG))
    return consumer
