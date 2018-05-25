# import ast
import io
import json
import sys
from time import sleep as Sleep

from spavro.datafile import DataFileReader
from spavro.io import DatumReader
from kafka import KafkaConsumer
from kafka.consumer.fetcher import NoOffsetForPartitionError


def pprint(obj):
    print(json.dumps(obj, indent=2))


def get_consumer(topic=None, strategy='latest'):
    consumer = KafkaConsumer(
        group_id='demo-reader',
        bootstrap_servers=['kafka-test:29092'],
        auto_offset_reset=strategy
    )
    if topic:
        consumer.subscribe(topic)
    return consumer


def connect_kafka():
    CONN_RETRY = 3
    CONN_RETRY_WAIT_TIME = 10
    for x in range(CONN_RETRY):
        try:
            consumer = get_consumer()
            topics = consumer.topics()
            consumer.close()
            print("Connected to Kafka...")
            return [topic for topic in topics]
        except Exception as ke:
            print("Could not connect to Kafka: %s" % (ke))
            Sleep(CONN_RETRY_WAIT_TIME)
    print("Failed to connect to Kafka after %s retries" % CONN_RETRY)
    sys.exit(1)  # Kill consumer with error


def seek_to_beginning(consumer):
    consumer.poll(timeout_ms=100, max_records=1)  # we have to poll to get the right partitions
    consumer.seek_to_beginning()                  # assigned to the consumer


def read_poll_result(poll_result, verbose=False):
    messages = []
    total_messages = 0
    for part, packages in poll_result.items():   # we don't worry about the partitions for now
        for package in packages:                 # a package can contain multiple messages
            # schema = None                        # serialzed with the same schema
            obj = io.BytesIO()
            obj.write(package.value)
            reader = DataFileReader(obj, DatumReader())

            # We can get the schema directly from the reader.
            # we get a mess of unicode that can't be json parsed so we need ast
            '''
            raw_schema = ast.literal_eval(str(reader.meta))
            schema = ast.literal_eval(str(raw_schema.get("avro.schema")))
            if not schema:
                raise AttributeError("No Schema serialized with message!")
            elif verbose:
                pprint(schema)
            '''
            for x, msg in enumerate(reader):  # multiple messages can arrive
                messages.append(msg)
                if verbose:                   # serialized in one package
                    pprint(msg)
                total_messages += 1
            obj.close()  # don't forget to close your open IO object.
    return messages


def read(consumer, start="LATEST", verbose=False, timeout_ms=5000, max_records=1000):
    messages = []
    if start not in ["FIRST", "LATEST"]:
        raise ValueError("%s it not a valid argument for 'start='" % start)
    if start is "FIRST":
        seek_to_beginning(consumer)
    while True:
        try:
            poll_result = consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        except NoOffsetForPartitionError as nofpe:
            print(nofpe)
            break
        if not poll_result:
            break
        new_messages = read_poll_result(poll_result, verbose)
        print(len(new_messages))
        messages.extend(new_messages)
    print("Read %s messages" % (len(messages)))
    return messages
