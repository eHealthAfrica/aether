import json
import requests

from aether.common.kernel import utils


def validate_pipeline(pipeline):
    '''
    Call kernel to check if the pipeline is valid and return the errors and
    entities.

    The expected return format is a list with two values, the first one is
    the list of errors and the second one the list of generated entities.

    The list of errors is also compounded as another list of two values, the
    first one is the wrong xpath included in any of the mapping rules, and the
    second one is the error message.

    ::

        (
            [
                ['xpath.wrong.1', 'reason 1'],
                ['xpath.wrong.2', 'reason 2'],
                ['xpath.wrong.3', 'reason 3'],
                # ...
            ],

            [
                { entity 1 },
                { entity 2 },
                { entity 3 },
                # ...
            ]
        )

    '''

    if not pipeline.mapping or not pipeline.input:
        return [], []

    # check kernel connection
    if not utils.test_connection():
        return (
            [['*', 'It was not possible to connect to Aether Kernel Server.']],
            [],
        )

    # validate the mapping rules
    # -------------------------------------------------------
    # kernel is expecting a payload with this format:
    # {
    #    "submission_payload": { json sample },
    #    "mapping_definition": {
    #      "entities": {
    #        "entity-type-name-1": None,
    #        "entity-type-name-2": None,
    #        "entity-type-name-3": None,
    #        ...
    #      },
    #      "mapping": [
    #        ["#!uuid", "xpath-entity-type-1-id"],
    #        ["xpath-input-1", "xpath-entity-type-1"],
    #        ["#!uuid", "xpath-entity-type-2-id"],
    #        ["xpath-input-2", "xpath-entity-type-2"],
    #        ...
    #      ],
    #    },
    #    "schemas": {
    #      "entity-type-name-1": { schema definition },
    #      "entity-type-name-2": { schema definition },
    #      "entity-type-name-3": { schema definition },
    #      ...
    #    },
    # }

    entities = {}
    schemas = {}
    for entity in pipeline.entity_types.all():
        entities[entity.name] = None
        schemas[entity.name] = entity.payload
    payload = {
        'submission_payload': pipeline.input,
        'mapping_definition': {
            'entities': entities,
            'mapping': pipeline.mapping,
        },
        'schemas': schemas,
    }

    try:
        kernerl_url = utils.get_kernel_server_url()
        resp = requests.post(
            url=f'{kernerl_url}/validate-mappings/',
            json=json.loads(json.dumps(payload)),
            headers=utils.get_auth_header(),
        )
        resp.raise_for_status()
        response = resp.json()
        return (
            response['mapping_errors'] if 'mapping_errors' in response else [],
            response['entities'] if 'entities' in response else [],
        )

    except Exception as e:
        return (
            [['*', f'It was not possible to validate the pipeline: {str(e)}']],
            []
        )
