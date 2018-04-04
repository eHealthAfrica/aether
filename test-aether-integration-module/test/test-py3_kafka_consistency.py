from . import *


@py3
def test_1_check_stream_entities(read_people, existing_entities):
    kernel_messages = [msg.get("payload").get("id") for msg in existing_entities.get(SEED_TYPE)]
    kafka_messages = [msg.get("id") for msg in read_people]
    assert(len(kernel_messages) == len(kafka_messages))
    for _id in kernel_messages:
        assert(_id in kafka_messages)
