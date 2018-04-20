import json
import requests

from aether.common.kernel import utils


def validate_pipeline(pipeline):
    '''
    Call kernel to check if the pipeline is valid and return the errors and
    entities.

    The expected return format is a list with two values, the first one is
    the list of errors and the second one the list of generated entities.

    The list of errors is a list of objects with two keys:
    - `path`, the wrong jsonpath included in any of the mapping rules,
    - `error_message` is the explanation.

    ::

        (
            [
                {'path': 'jsonpath.wrong.1', 'error_message': 'Reason 1'},
                {'path': 'jsonpath.wrong.2', 'error_message': 'Reason 2'},
                {'path': 'jsonpath.wrong.3', 'error_message': 'Reason 3'},
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

    if not pipeline.input or not pipeline.mapping or not pipeline.entity_types:
        return [], []

    # check kernel connection
    if not utils.test_connection():
        return (
            [{'error_message': 'It was not possible to connect to Aether Kernel Server.'}],
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
    #        ["#!uuid", "jsonpath-entity-type-1-id"],
    #        ["jsonpath-input-1", "jsonpath-entity-type-1"],
    #        ["#!uuid", "jsonpath-entity-type-2-id"],
    #        ["jsonpath-input-2", "jsonpath-entity-type-2"],
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
    for entity_type in pipeline.entity_types:
        name = entity_type['name']
        entities[name] = None
        schemas[name] = entity_type

    mapping = [
        [rule['source'], rule['destination']]
        for rule in pipeline.mapping
    ]

    payload = {
        'submission_payload': pipeline.input,
        'mapping_definition': {
            'entities': entities,
            'mapping': mapping,
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
            [{'error_message': f'It was not possible to validate the pipeline: {str(e)}'}],
            []
        )
