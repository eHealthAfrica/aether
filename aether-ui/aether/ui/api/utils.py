
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

from django.utils import timezone
from django.utils.translation import ugettext as _

from rest_framework import status

from aether.common.kernel import utils


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
            [{'description': _('It was not possible to connect to Aether Kernel.')}],
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
        entities[name] = str(uuid.uuid4())  # the value must be UUID complaint
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
        description = _('It was not possible to validate the pipeline: {}').format(str(data))
        errors = [{'description': description}]
        return (errors, [])


def kernel_to_pipeline():
    '''
    Fetches all mappingsets in kernel and tranform them into pipelines,
    taking also the linked mappings+schemas and transform them into contracts.
    '''
    KERNEL_URL = utils.get_kernel_server_url()

    mappingsets = utils.get_all_docs(f'{KERNEL_URL}/mappingsets/')
    for mappingset in mappingsets:
        mappingset_id = mappingset['id']

        if models.Pipeline.objects.filter(mappingset=mappingset_id).count() > 0:
            # do not update the current pipeline but bring new contracts
            pipeline = models.Pipeline.objects.filter(mappingset=mappingset_id).first()
        else:
            # create the pipeline
            pipeline = models.Pipeline.objects.create(
                id=mappingset_id,  # use mappingset id as pipeline id
                name=mappingset['name'],
                schema=mappingset['schema'],
                input=mappingset['input'],
                mappingset=mappingset_id,
            )

        # fetch linked mappings
        url = f'{KERNEL_URL}/mappings/?mappingset={mappingset_id}'
        mappings = utils.get_all_docs(url)

        for mapping in mappings:
            mapping_id = mapping['id']

            if models.Contract.objects.filter(kernel_refs__mapping=mapping_id).count() > 0:
                # do not update the current contract
                continue

            schemas_url = f'{KERNEL_URL}/schemas/?fields=definition&mapping={mapping_id}'

            models.Contract.objects.create(
                id=mapping_id,  # use mapping id as contract id
                name=mapping['name'],
                pipeline=pipeline,

                mapping=[
                    {'id': str(uuid.uuid4()), 'source': rule[0], 'destination': rule[1]}
                    for rule in mapping['definition']['mapping']
                ],
                entity_types=[
                    schema['definition']
                    for schema in utils.get_all_docs(schemas_url)
                ],

                is_active=mapping['is_active'],
                is_read_only=mapping['is_read_only'],

                kernel_refs={
                    'project': mapping['project'],
                    'mapping': mapping_id,
                    'schemas': mapping['definition']['entities'],
                },
                published_on=mapping['modified'],
            )


def publish_preflight(contract):
    '''
    Performs a check for possible contract publish errors against kernel
    '''

    def get_from_kernel_by_id(model, pk):
        try:
            return kernel_data_request(f'{model}/{pk}/')
        except Exception:
            return None

    def get_from_kernel_by_name(model, name):
        try:
            results = kernel_data_request(f'{model}/?name={name}')
            if results['count'] > 0:
                return results['results'][0]
            return None
        except Exception:  # pragma: no cover
            return None

    outcome = {
        'successful': [],
        'error': [],
        'exists': [],
        'ids': {
            'mapping': {},
            'schema': {},
        }
    }

    if contract.mapping_errors:
        outcome['error'].append(_('{} mappings have errors'.format(contract.name)))
        return outcome

    # check entity types (schemas in kernel)
    for entity_type in contract.entity_types:
        name = entity_type['name']
        id = contract.kernel_refs.get('schemas', {}).get(name) if contract.kernel_refs else None

        if id and get_from_kernel_by_id('schemas', id):
            outcome['exists'].append({
                name: _('Entity type (schema) with id {} exists on kernel').format(id)
            })
            outcome['ids']['schema'][name] = id
        else:
            get_by_name = get_from_kernel_by_name('schemas', name)
            if get_by_name:
                outcome['exists'].append({
                    name: _('Entity type (schema) with name {} exists on kernel').format(name)
                })
                outcome['ids']['schema'][name] = get_by_name['id']

    # check the contract (mapping in kernel)
    if contract.kernel_refs and get_from_kernel_by_id('mappings', contract.kernel_refs.get('mapping')):
        id = contract.kernel_refs['mapping']
        outcome['exists'].append({
            contract.name: _('Contract (mapping) with id {} exists on kernel').format(id)
        })
        outcome['ids']['mapping'][contract.name] = id
    else:
        get_by_name = get_from_kernel_by_name('mappings', contract.name)
        if get_by_name:
            outcome['exists'].append({
                contract.name: _('Contract (mapping) with name {} exists on kernel.').format(contract.name)
            })
            outcome['ids']['mapping'][contract.name] = get_by_name['id']

    # check the pipeline (mappingset in kernel)
    pipeline = contract.pipeline
    if pipeline.mappingset:
        mappingset = get_from_kernel_by_id('mappingsets', pipeline.mappingset)
        if mappingset:
            if json.dumps(mappingset['input'], sort_keys=True) != json.dumps(pipeline.input, sort_keys=True):
                outcome['exists'].append({
                    pipeline.name: _('Input data will be changed')
                })
            if json.dumps(mappingset['schema'], sort_keys=True) != json.dumps(pipeline.schema, sort_keys=True):
                outcome['exists'].append({
                    pipeline.name: _('Schema data will be changed')
                })

    return outcome


def publish_contract(project_name, contract, objects_to_overwrite={}):
    '''
    Transform pipeline and contract to kernel artefacts and publish
    '''

    pipeline = contract.pipeline
    mappingset_id = str(pipeline.mappingset or uuid.uuid4())
    mapping_id = objects_to_overwrite.get('mapping', {}).get(contract.name, str(contract.id))

    # find out linked project id
    project_id = None

    # use pipeline mappingset as first source of truth
    if pipeline.mappingset:
        try:
            mappingset = kernel_data_request(f'mappingsets/{pipeline.mappingset}/')
            project_id = mappingset.get('project')
        except Exception:
            pass

    # try with the linked project (if contract was published before)
    if not project_id and contract.kernel_refs and contract.kernel_refs.get('project'):
        try:
            project_pk = contract.kernel_refs['project']
            project = kernel_data_request(f'projects/{project_pk}/?fields=name')

            project_id = project_pk
            project_name = project.get('name')
        except Exception:
            pass

    if not project_id:
        # try with the given project name
        try:
            results = kernel_data_request(f'projects/?fields=id&name={project_name}')
            if results['count'] == 1:  # it can only be one
                project_id = results['results'][0]['id']
        except Exception:  # pragma: no cover
            pass

    if not project_id:  # set a new value
        project_id = str(uuid.uuid4())

    # build schemas from contract entities, include a new id if missing
    schemas = [
        {
            'id': objects_to_overwrite.get('schema', {}).get(entity_type.get('name'), str(uuid.uuid4())),
            'name': entity_type.get('name'),
            'definition': entity_type,
        }
        for entity_type in contract.entity_types
    ]
    entities = {schema['name']: schema['id'] for schema in schemas}

    # payload to POST to kernel with the contract artefacts
    data = {
        'name': project_name,

        # the contract entity types correspond to kernel schemas
        'schemas': schemas,

        # the pipelines have a 1:1 relationship with kernel mappingsets
        'mappingsets': [{
            'id': mappingset_id,
            'name': pipeline.name,
            'input': pipeline.input,
            'schema': pipeline.schema,
        }],

        # the contract mapping corresponds to kernel mapping but with different rules format
        'mappings': [{
            'id': mapping_id,
            'name': contract.name,
            'definition': {
                'mapping': [
                    [rule['source'], rule['destination']]
                    for rule in contract.mapping
                ],
                'entities': entities,
            },
            'mappingset': mappingset_id,
            'is_active': True,
            'is_ready_only': contract.is_read_only,
        }],
    }

    try:
        result = kernel_data_request(f'projects/{project_id}/artefacts/', 'patch', data)

        # update pipeline
        pipeline.mappingset = mappingset_id
        pipeline.save()

        kernel_refs = {
            'project': result['project'],
            'mapping': mapping_id,  # 1:1
            'schemas': entities,
        }

        contract.published_on = timezone.now()
        contract.kernel_refs = kernel_refs
        contract.save()

        return {'artefacts': kernel_refs}

    except Exception as e:
        return {'error': str(e)}


################################################################################
# HELPERS
################################################################################


def kernel_data_request(url='', method='get', data=None):
    '''
    Handle requests to the kernel server
    '''

    res = requests.request(
        method=method,
        url=f'{utils.get_kernel_server_url()}/{url}',
        json=data or {},
        headers=utils.get_auth_header(),
    )

    if res.status_code == 204:  # NO-CONTENT
        return None

    if res.status_code >= 200 and res.status_code < 400:
        return res.json()
    else:
        raise Exception(res.json())
