
# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import requests
import uuid

from rest_framework import status

from aether.common.kernel import utils
from urllib.parse import urlparse


from . import models


def validate_contract(contract):
    '''
    Call kernel to check if the contract is valid and return the errors and
    entities.

    The expected return format is a list with two values, the first one is
    the list of errors and the second one the list of generated entities.

    The list of errors is a list of objects with these keys:
    - `description` (always) is the error explanation,
    - `path` (optional) the wrong jsonpath included in any of the mapping rules,
    - `data` (optional) the extracted entity that cannot be used yet. This appears
      along with the `description` "Extracted record did not conform to registered schema".

    ::

        (
            [
                {'path': 'jsonpath.wrong.1', 'description': 'Reason 1'},
                {'path': 'jsonpath.wrong.2', 'description': 'Reason 2'},
                {'path': 'jsonpath.wrong.3', 'description': 'Reason 3'},
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

    if not contract.pipeline.input or not contract.mapping or not contract.entity_types:
        return [], []

    # check kernel connection
    if not utils.test_connection():
        return (
            [{'description': 'It was not possible to connect to Aether Kernel.'}],
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
    for entity_type in contract.entity_types:
        name = entity_type['name']
        entities[name] = None
        schemas[name] = entity_type

    mapping = [
        [rule['source'], rule['destination']]
        for rule in contract.mapping
    ]

    payload = {
        'submission_payload': contract.pipeline.input,
        'mapping_definition': {
            'entities': entities,
            'mapping': mapping,
        },
        'schemas': schemas,
    }
    kernel_url = utils.get_kernel_server_url()
    resp = requests.post(
        url=f'{kernel_url}/validate-mappings/',
        json=json.loads(json.dumps(payload)),
        headers=utils.get_auth_header(),
    )
    if resp.status_code == status.HTTP_200_OK:
        data = resp.json()
        errors = data.get('mapping_errors', [])
        output = data.get('entities', [])
        return (errors, output)
    # The 400 response we get from the restframework serializers is a
    # dictionary. The keys are serializer field names and the values are
    # lists of errors. Concatenate all lists and return the result as
    # `errors`.
    elif resp.status_code == status.HTTP_400_BAD_REQUEST:
        data = resp.json()
        errors = []
        for error_group in data.values():
            for error_detail in error_group:
                error = {'description': str(error_detail)}
                errors.append(error)
        return (errors, [])
    else:
        data = resp.text
        description = f'It was not possible to validate the pipeline: {str(data)}'
        errors = [{'description': description}]
        return (errors, [])


def kernel_data_request(url='', method='get', data=None):
    '''
    Handle requests to the kernel server
    '''
    if data is None:
        data = {}
    kernerl_url = utils.get_kernel_server_url()
    res = requests.request(method=method,
                           url=f'{kernerl_url}/{url}',
                           headers=utils.get_auth_header(),
                           json=data
                           )
    if res.status_code >= 200 and res.status_code < 400:
        return res.json()
    else:
        raise Exception(res.json())


def is_object_linked(kernel_refs, object_name, entity_type_name=''):
    if kernel_refs and object_name in kernel_refs:
        try:
            if object_name is 'schemas':
                if entity_type_name in kernel_refs[object_name]:
                    url = f'{object_name.lower()}/{kernel_refs[object_name][entity_type_name]}'
                else:
                    return False
            else:
                url = f'{object_name.lower()}/{kernel_refs[object_name]}/'
            kernel_data_request(url, 'get')
            return True
        except Exception:
            return False
    else:
        return False


def publish_preflight(pipeline, project_name, outcome, contract):
    '''
    Performs a check for possible pipeline publish errors against kernel
    '''
    if contract.mapping_errors:
        outcome['error'].append('{} mappings have errors'.format(contract.name))
        return outcome
    for entity_type in contract.entity_types:
        if is_object_linked(contract.kernel_refs, 'schemas', entity_type['name']):
            outcome['exists'].append({entity_type['name']: '{} schema with id {} exists'.format(
                                        entity_type['name'],
                                        contract.kernel_refs['schemas'][entity_type['name']])})
            outcome['ids']['schema'][entity_type['name']] = contract.kernel_refs['schemas'][entity_type['name']]
        else:
            get_by_name = kernel_data_request(f'schemas/?name={entity_type["name"]}')['results']
            if len(get_by_name):
                outcome['exists'].append({entity_type['name']: 'Schema with name {} exists on kernel'.format(
                                        entity_type['name'])})
                outcome['ids']['schema'][entity_type['name']] = get_by_name[0]['id']
    if is_object_linked(contract.kernel_refs, 'mappings'):
        outcome['exists'].append({contract.name: 'Mapping with id {} exists'.format(
                                        contract.kernel_refs['mappings'])})
        outcome['ids']['mapping'][contract.name] = contract.kernel_refs['mappings']
    else:
        get_by_name = kernel_data_request(f'mappings/?name={contract.name}')['results']
        if len(get_by_name):
            outcome['exists'].append({contract.name: 'Pipeline (mapping) with name {} exists on kernel.'.format(
                                    contract.name)})
            outcome['ids']['mapping'][contract.name] = get_by_name[0]['id']

    if pipeline.mappingset:
        try:
            mappingset = kernel_data_request(f'mappingsets/{pipeline.mappingset}/')
            if json.dumps(mappingset['input'], sort_keys=True) != json.dumps(pipeline.schema, sort_keys=True):
                outcome['exists'].append({pipeline.name: 'Input data will be changed'})
        except Exception as e:
            print(str(e))
    return outcome


def publish_pipeline(pipeline, projectname, contract, objects_to_overwrite={}):
    '''
    Transform pipeline and contract to kernel artefacts and publish
    '''
    project_id = str(uuid.uuid4())
    project_name = 'Aux'
    mappingsets = []
    mappings = []
    schemas = []
    outcome = {}
    try:
        projects = kernel_data_request(f'projects/?name=Aux')['results']
        aux_project = projects[0] if len(projects) else {}
        project_id = aux_project.get('id', str(uuid.uuid4()))
        project_name = aux_project.get('name', 'Aux')
    except Exception as e:
        print(f'Error: {str(e)}')
    mappingset = {}
    if pipeline.mappingset:
        try:
            mappingset = kernel_data_request(f'mappingsets/{pipeline.mappingset}/')
            project_id = mappingset.get('project')
            mappingset['name'] = pipeline.name
            mappingset['input'] = pipeline.schema
        except Exception as e:
            print(str(e))
            mappingset = {
                'id': str(pipeline.mappingset),
                'name': pipeline.name,
                'input': pipeline.schema,
            }
    else:
        mappingset = {
            'id': str(uuid.uuid4()),
            'name': pipeline.name,
            'input': pipeline.schema,
        }
    mappingsets.append(mappingset)
    [
        schemas.append({
            'name': schema.get('name'),
            'type': schema.get('type'),
            'definition': schema,
            'id': objects_to_overwrite.get('schema', {}).get(schema.get('name'))
        })
        for schema in contract.entity_types
    ]
    mappings.append({
        'id': objects_to_overwrite.get('mapping', {}).get(contract.name, str(contract.id)),
        'name': contract.name,
        'definition': {
            'mapping': [
                [rule['source'], rule['destination']]
                for rule in contract.mapping
            ]
        },
        'mappingset': mappingsets[0]['id'],
        'is_active': True,
        'is_ready_only': contract.is_read_only
    })
    try:
        data = {
            'name': project_name,
            'schemas': schemas,
            'mappingsets': mappingsets,
            'mappings': mappings
        }
        result = kernel_data_request(f'projects/{project_id}/artefacts/', 'patch', data)
        if 'schemas' in result:
            _schemas = {}
            for id in result['schemas']:
                try:
                    schema_data = kernel_data_request(f'schemas/{id}/')
                    schema_name = schema_data.get('name')
                    _schemas[schema_name] = id
                except Exception as ex:
                    print(f'Error {str(ex)}')
            result['schemas'] = _schemas
        if 'mappings' in result and len(result['mappings']):
            result['mappings'] = result['mappings'][0]
        outcome['artefacts'] = result
    except Exception as e:
        print(f'Error: {str(e)}')
        outcome['error'] = str(e)
    return outcome


def convert_mappings(mapping_from_kernel):
    return [
        {'source': mapping[0], 'destination': mapping[1]}
        for mapping in mapping_from_kernel
    ]


def convert_entity_types(entities_from_kernel):
    result = {'schemas': [], 'ids': {}}
    for _, entity_id in entities_from_kernel.items():
        project_schema = kernel_data_request(f'projectschemas/{entity_id}/')
        schema = kernel_data_request(f'schemas/{project_schema["schema"]}/')
        result['schemas'].append(schema['definition'])
        result['ids'][schema['name']] = schema['id']
    return result


def create_new_pipeline_from_kernel(mappingset):
    new_pipeline = linked_pipeline_object('mappingset', mappingset['id'])
    mappings = kernel_data_request('mappings/?mappingset={}'.format(mappingset['id']))['results']
    if not new_pipeline and len(mappings):
        new_pipeline = models.Pipeline.objects.create(
            id=mappingset['id'],
            name=mappingset['name'],
            schema=mappingset['input'],
            mappingset=mappingset['id']
        )
    else:
        new_pipeline = new_pipeline.first()
    for mapping in mappings:
        new_mapping = linked_pipeline_object('mapping', mapping['id'])
        if not new_mapping:
            entity_types = convert_entity_types(mapping['definition']['entities'])
            models.Contract.objects.create(
                id=mapping['id'],
                name=mapping['name'],
                mapping=convert_mappings(mapping['definition']['mapping']),
                entity_types=entity_types['schemas'],
                pipeline=new_pipeline,
                is_active=mapping['is_active'],
                is_read_only=mapping['is_read_only'],
                kernel_refs={
                    'schemas': entity_types['ids'],
                    'mappings': [mapping['id']]
                },
                published_on=mapping['modified']
            )
    return new_pipeline


def linked_pipeline_object(object_name, id):
    if object_name is 'mappingset':
        return models.Pipeline.objects.filter(mappingset=id)
    else:
        kwargs = {
            '{0}__{1}'.format('kernel_refs', object_name): id
        }
        return models.Contract.objects.filter(**kwargs)


def kernel_to_pipeline():
    mappingsets_response = kernel_data_request('mappingsets/')
    pipelines = []
    while True:
        mappingsets = mappingsets_response['results']
        for mappingset in mappingsets:
            pipelines.append(create_new_pipeline_from_kernel(mappingset))
        if mappingsets_response['next']:
            url_segments = urlparse(mappingsets_response['next'])
            mappingsets_response = kernel_data_request('{}?{}'.format(url_segments.path, url_segments.query)[1:])
        else:
            break
    return pipelines
