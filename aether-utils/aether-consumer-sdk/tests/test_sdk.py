from . import *
from aether.consumer import KafkaConsumer

def pprint(obj):
    print(json.dumps(obj, indent=2))

def test_boolean_pass(messages_test_boolean_pass):
    topic = "TestBooleanPass"
    messages = messages_test_boolean_pass
    assert(len(messages) == topic_size), "Should have generated the right number of messages"
    consumer_kwargs = {
        "aether_masking_schema_annotation" : "aetherMaskingLevel",
        "aether_masking_schema_levels" : [1,2,3,4,5],
        "bootstrap_servers" : kafka_server,
        "heartbeat_interval_ms" : 2500,
        "session_timeout_ms" : 18000,
        "request_timeout_ms" : 20000,
        "auto_offset_reset" : 'latest',
        "consumer_timeout_ms" : 17000
    }
    for emit_level in range(1,6):
        consumer_kwargs["aether_masking_schema_emit_level"] = emit_level
        consumer = KafkaConsumer(**consumer_kwargs)
        consumer.subscribe(topic)
        consumer.seek_to_beginning()
        new_messages = consumer.poll_and_deserialize(timeout_ms=10000, max_records=1000)
        count =  0
        for partition, packages in new_messages.items():
            for package in packages:
                schema = package.get("schema")
                for msg in package.get("messages"):
                    count += 1
                    print(partition)
                    pprint(msg)
        print(count)
        consumer.close()


def test_enum_pass(messages_test_enum_pass):
    topic = "TestEnumPass"
    messages = messages_test_enum_pass
    assert(len(messages) == topic_size), "Should have generated the right number of messages"
