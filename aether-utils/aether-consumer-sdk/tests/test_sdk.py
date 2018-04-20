from . import *
from aether.consumer import KafkaConsumer


@pytest.mark.parametrize("emit_level,unmasked_fields", [
    (0, 2),
    (1, 3),
    (2, 4),
    (3, 5),
    (4, 6),
    (5, 7),
])
@pytest.mark.integration
def test_masking_boolean_pass(messages_test_boolean_pass, emit_level, unmasked_fields):
    topic = "TestBooleanPass"
    assert(len(messages_test_boolean_pass) == topic_size), "Should have generated the right number of messages"
    # set configs
    consumer_kwargs = {
        "aether_masking_schema_annotation": "aetherMaskingLevel",
        "aether_emit_flag_field_path": "$.publish",
        "aether_emit_flag_values": [True, False],
        "aether_masking_schema_levels": [0, 1, 2, 3, 4, 5],
        "aether_masking_schema_emit_level" : emit_level,  # set by test params
        "bootstrap_servers": kafka_server,
        "heartbeat_interval_ms": 2500,
        "session_timeout_ms": 18000,
        "request_timeout_ms": 20000,
        "auto_offset_reset": 'latest',
        "consumer_timeout_ms": 17000
    }
    # get messages for this emit level
    iter_consumer = KafkaConsumer(**deepcopy(consumer_kwargs))
    iter_consumer.subscribe(topic)
    iter_consumer.seek_to_beginning()
    messages = iter_consumer.poll_and_deserialize(timeout_ms=10000, max_records=1000)
    iter_consumer.close()
    # read messages and check masking
    for partition, packages in messages.items():
        for package in packages:
            schema = package.get("schema")
            for msg in package.get("messages"):
                assert(len(msg.keys()) ==
                       unmasked_fields), "%s fields should be unmasked" % unmasked_fields


@pytest.mark.parametrize("publish_on, expected_count", [
    ([True], int(topic_size/2)),
    ([False], int(topic_size/2)),
    ([True, False], topic_size),
    (True, int(topic_size/2)),
    (False, int(topic_size/2))
])
@pytest.mark.integration
def test_publishing_boolean_pass(messages_test_boolean_pass, publish_on, expected_count):
    topic = "TestBooleanPass"
    assert(len(messages_test_boolean_pass) == topic_size), "Should have generated the right number of messages"
    # set configs
    consumer_kwargs = {
        "aether_masking_schema_annotation": "aetherMaskingLevel",
        "aether_emit_flag_field_path": "$.publish",
        "aether_emit_flag_values": publish_on,
        "aether_masking_schema_levels": [0, 1, 2, 3, 4, 5],
        "aether_masking_schema_emit_level" : 5,
        "bootstrap_servers": kafka_server,
        "heartbeat_interval_ms": 2500,
        "session_timeout_ms": 18000,
        "request_timeout_ms": 20000,
        "auto_offset_reset": 'latest',
        "consumer_timeout_ms": 17000
    }
    # get messages for this emit level
    iter_consumer = KafkaConsumer(**deepcopy(consumer_kwargs))
    iter_consumer.subscribe(topic)
    iter_consumer.seek_to_beginning()
    messages = iter_consumer.poll_and_deserialize(timeout_ms=10000, max_records=1000)
    iter_consumer.close()
    # read messages and check masking
    count = 0
    for partition, packages in messages.items():
        for package in packages:
            schema = package.get("schema")
            for msg in package.get("messages"):
                count +=1
    assert(count == expected_count), "unexpected # of messages published"


@pytest.mark.integration
def test_enum_pass(messages_test_enum_pass):
    topic = "TestEnumPass"
    messages = messages_test_enum_pass
    assert(len(messages) == topic_size), "Should have generated the right number of messages"


@pytest.mark.unit
@pytest.mark.parametrize("field_path,field_value,pass_msg,fail_msg", [
    (None, None, {"approved": True}, {"approved": False}),
    ("$.checked", None, {"checked": True}, {"checked": False}),
    (None, [False], {"approved": False}, {"approved": True}),
    (None, ["yes", "maybe"], {"approved": "yes"}, {"approved": "no"}),
    (None, ["yes", "maybe"], {"approved": "maybe"}, {"approved": "no"}),
    (None, ["yes", "maybe"], {"approved": "maybe"}, {"checked": "maybe"})
])
def test_get_approval_filter(offline_consumer, field_path, field_value, pass_msg, fail_msg):
    if field_path:
        offline_consumer._add_config({"aether_emit_flag_field_path": field_path})
    if field_value:
        offline_consumer._add_config({"aether_emit_flag_values": field_value})
    _filter = offline_consumer.get_approval_filter()
    assert(_filter(pass_msg))
    assert(_filter(fail_msg) is not True)


@pytest.mark.unit
@pytest.mark.parametrize("emit_level", [
    (0),
    (1),
    (2),
    (3),
    (4),
    (5)
])
@pytest.mark.unit
def test_msk_msg_default_map(offline_consumer, sample_schema, sample_message, emit_level):
    offline_consumer._add_config({"aether_masking_schema_emit_level": emit_level})
    mask = offline_consumer.get_mask_from_schema(sample_schema)
    masked = mask(sample_message)
    assert(len(masked.keys()) == (emit_level + 2)), ("%s %s" % (emit_level, masked))


@pytest.mark.unit
@pytest.mark.parametrize("emit_level,expected_count", [
    ("public", 3),
    ("confidential", 4),
    ("secret", 5),
    ("top secret", 6),
    ("ufos", 7)
])
@pytest.mark.parametrize("possible_levels", [([
    "public",
    "confidential",
    "secret",
    "top secret",
    "ufos"
])])
def test_msk_msg_custom_map(offline_consumer, sample_schema_top_secret, sample_message_top_secret, emit_level, possible_levels, expected_count):
    offline_consumer._add_config({"aether_masking_schema_emit_level": emit_level})
    offline_consumer._add_config({"aether_masking_schema_levels": possible_levels})
    mask = offline_consumer.get_mask_from_schema(sample_schema_top_secret)
    masked = mask(sample_message_top_secret)
    assert(len(masked.keys()) == (expected_count)), ("%s %s" % (emit_level, masked))
