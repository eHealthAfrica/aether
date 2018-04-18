import io
import json
import pytest
import sys

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from spavro.datafile import DataFileWriter
from spavro.io import DatumWriter
from spavro.schema import parse as ParseSchema
from time import sleep

from .assets.schemas import test_schemas

print(test_schemas)

kafka_server = "kafka-test:29092"
kafka_connection_retry = 10
kafka_connection_retry_wait = 6
topic_size = 100

def send_messages(producer, name, schema, messages):
    bytes_writer = io.BytesIO()
    writer = DataFileWriter(bytes_writer, DatumWriter(), schema, codec='deflate')
    for msg in messages:
        writer.append(msg)
    writer.flush()
    raw_bytes = bytes_writer.getvalue()
    writer.close()
    future = producer.send(name, key=str(msg.get("id")), value=raw_bytes)
    #block until it actually sends.
    record_metadata = future.get(timeout=10)
    producer.flush()

def write_to_topic(schema_name):
    producer = None
    for x in range(kafka_connection_retry):
        try:
            producer = KafkaProducer(bootstrap_servers=kafka_server, acks=1, key_serializer=str.encode)
            break
        except NoBrokersAvailable:
            sleep(kafka_connection_retry_wait)
    if not producer:
        raise NoBrokersAvailable("Could not attach to kafka after %s seconds. Check configuration" %
                                 (kafka_connection_retry * kafka_connection_retry_wait))
    assets = test_schemas.get(schema_name)
    schema = assets.get("schema")
    schema = ParseSchema(json.dumps(schema))
    mocker = assets.get("mocker")
    messages = mocker(count=topic_size)
    send_messages(producer, schema_name, schema, messages)
    producer.close()
    return messages


@pytest.fixture(scope="session")
def messages_test_boolean_pass():
    messages = write_to_topic("TestBooleanPass")
    return messages

@pytest.fixture(scope="session")
def messages_test_enum_pass():
    messages = write_to_topic("TestEnumPass")
    return messages
