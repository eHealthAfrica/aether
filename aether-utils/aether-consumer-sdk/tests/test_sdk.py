from . import *
from aether.consumer import KafkaConsumer

@pytest.mark.integration
def test_boolean_pass(messages_test_boolean_pass):
    topic = "TestBooleanPass"
    messages = messages_test_boolean_pass
    assert(len(messages) == topic_size), "Should have generated the right number of messages"
    consumer_kwargs = {
        "aether_masking_schema_annotation" : "aetherMaskingLevel",
        "aether_emit_flag_field_path": "$.publish",
        "aether_emit_flag_values": [True, False],
        "aether_masking_schema_levels" : [1,2,3,4,5],
        "bootstrap_servers" : kafka_server,
        "heartbeat_interval_ms" : 2500,
        "session_timeout_ms" : 18000,
        "request_timeout_ms" : 20000,
        "auto_offset_reset" : 'latest',
        "consumer_timeout_ms" : 17000
    }
    messages = {}  #  emit_level : {returned from topic}
    for emit_level in range(1,6):
        # get messages for this emit level
        consumer_kwargs["aether_masking_schema_emit_level"] = emit_level
        consumer = KafkaConsumer(**consumer_kwargs)
        consumer.subscribe(topic)
        consumer.seek_to_beginning()
        new_messages = consumer.poll_and_deserialize(timeout_ms=10000, max_records=1000)
        messages[emit_level] = new_messages
        consumer.close()

    # expectations for assertions: emit_level == #of fields present; half of messages publishable
    expectations = [[emit_level, 50, emit_level] for emit_level in range(1,6)]
    for emit_level, expected_count, unmasked_fields in expectations:
        new_messages = messages[emit_level]
        for partition, packages in new_messages.items():
            for package in packages:
                schema = package.get("schema")
                for msg in package.get("messages"):
                    count += 1
                    assert(len(msg.keys()) == unmasked_fields), "%s fields should be unmasked" % unmasked_fields
        assert(count == topic_size), "Half of the messages messages should pass"

@pytest.mark.integration
def test_enum_pass(messages_test_enum_pass):
    topic = "TestEnumPass"
    messages = messages_test_enum_pass
    assert(len(messages) == topic_size), "Should have generated the right number of messages"

@pytest.mark.unit
def test_publish(offline_consumer):
    consumer = offline_consumer
    assert(len(consumer.config.keys()) > 2)

@pytest.mark.unit
def test_get_approval_filter_default(offline_consumer):
    default_filter = offline_consumer.get_approval_filter()
    pass_msg = {"approved": True}
    fail_msg = {"approved": False}
    assert(default_filter(pass_msg))
    assert(default_filter(fail_msg) is not True)

@pytest.mark.unit
def test_get_approval_filter_new_watch_word(offline_consumer):
    offline_consumer._add_config({
        "aether_emit_flag_field_path": "$.checked"
    })
    new_filter = offline_consumer.get_approval_filter()
    pass_msg = {"checked": True}
    fail_msg = {"checked": False}
    assert(new_filter(pass_msg))
    assert(new_filter(fail_msg) is not True)

@pytest.mark.unit
def test_get_approval_filter_new_watch_condition(offline_consumer):
    offline_consumer._add_config({
        "aether_emit_flag_values": [False]
    })
    new_filter = offline_consumer.get_approval_filter()
    pass_msg = {"approved": False}
    fail_msg = {"approved": True}
    assert(new_filter(pass_msg))
    assert(new_filter(fail_msg) is not True)
