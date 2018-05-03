import json
import requests
import ast

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


def kernel_data_request(url, method, data={}):
    '''
    Handle post requests to the kernel server
    '''
    kernerl_url = utils.get_kernel_server_url()
    res = requests.request(method=method,
                           url=f'{kernerl_url}/{url.lower()}/',
                           headers=utils.get_auth_header(),
                           json=data
                           )
    if res.status_code >= 200 and res.status_code < 400:
        return res.json()
    else:
        raise Exception(res.json())


def create_new_kernel_object(object_name, pipeline, data={}, project_name='Aux', entity_name=None):
    try:
        res = kernel_data_request(f'{object_name}s', 'post', data)
    except Exception as e:
        error = ast.literal_eval(str(e))
        error['object_name'] = data['name'] if 'name' in data else 'unknown'
        raise Exception(error)
    if not pipeline.kernel_refs:
        pipeline.kernel_refs = {}
    if object_name is 'schema' or object_name is 'projectSchema':
        if object_name not in pipeline.kernel_refs:
            pipeline.kernel_refs[object_name] = {}
        pipeline.kernel_refs[object_name][entity_name if entity_name is not None else data['name']] = res['id']
        pipeline.save()
        if object_name is 'schema':
            create_project_schema_object('{}-{}'.format(project_name, data['name']),
                                         pipeline, res['id'], data['name'])
    else:
        pipeline.kernel_refs[object_name] = res['id']
        pipeline.save()


def is_object_linked(kernel_refs, object_name, entity_type_name=''):
    if kernel_refs and object_name in kernel_refs:
        try:
            if object_name is 'schema' or object_name is 'projectSchema':
                if entity_type_name in kernel_refs[object_name]:
                    url = f'{object_name}s/{kernel_refs[object_name][entity_type_name]}'
                else:
                    return False
            else:
                url = f'{object_name}s/{kernel_refs[object_name]}'
            kernel_data_request(url, 'get')
            return True
        except Exception:
            return False
    else:
        return False


def create_project_schema_object(name, pipeline, schema_id, entity_name):
    project_schema_data = {
                            'name': name,
                            'mandatory_fields': '[]',
                            'transport_rule': '[]',
                            'masked_fields': '[]',
                            'is_encrypted': False,
                            'project': pipeline.kernel_refs['project'],
                            'schema': schema_id
                        }
    if not is_object_linked(pipeline.kernel_refs, 'projectSchema', entity_name):
        create_new_kernel_object('projectSchema',
                                 pipeline, project_schema_data, entity_name=entity_name)
