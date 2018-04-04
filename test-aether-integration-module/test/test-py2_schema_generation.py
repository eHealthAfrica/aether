from . import *


@py2
def test_1_register_schemas(schema_registration):
    assert(schema_registration)  # Try to use the test mode of the wizard


@py2
def test_2_check_schemas(existing_schemas):
    assert(len(existing_schemas) > 0)
