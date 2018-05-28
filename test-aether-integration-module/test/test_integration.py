from . import *


####################################################################################
#  Create Schemas -> Entities -> Produce -> Check in Kafka for result
####################################################################################


def test_1_register_schemas(schema_registration):
    assert(schema_registration)  # Try to use the test mode of the wizard


def test_2_check_schemas(existing_schemas):
    assert(len(existing_schemas) > 0)


def test_3_generate_entities(generate_entities):
    assert(len(generate_entities) == SEED_ENTITIES)


def test_4_check_updated_count(existing_entities, generate_entities):
    assert(len(existing_entities.get(SEED_TYPE)) >= SEED_ENTITIES)


def test_5_check_stream_entities(read_people, existing_entities):
    kernel_messages = [msg.get("payload").get("id") for msg in existing_entities.get(SEED_TYPE)]
    kafka_messages = [msg.get("id") for msg in read_people]
    assert(len(kernel_messages) == len(kafka_messages))
    for _id in kernel_messages:
        assert(_id in kafka_messages)
