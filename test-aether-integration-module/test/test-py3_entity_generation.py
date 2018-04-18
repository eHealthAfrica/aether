from . import *


@py3
def test_1_generate_entities(generate_entities):
    assert(len(generate_entities) == SEED_ENTITIES)


@py3
def test_2_check_updated_count(existing_entities, generate_entities):
    assert(len(existing_entities.get(SEED_TYPE)) >= SEED_ENTITIES)
