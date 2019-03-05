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
import uuid


from django.utils import timezone
from django.utils.translation import ugettext as _

from rest_framework import status

from aether.common.kernel import utils
from aether.common.utils import request

from . import models


MSG_CONTRACT_VALIDATION_ERROR = _('It was not possible to validate the contract: {}')
MSG_CONTRACT_VALIDATION_KERNEL_ERROR = _('It was not possible to connect to Aether Kernel.')

MSG_PROJECT_IN_KERNEL = _('Project is already published')
MSG_PROJECT_NOT_IN_KERNEL = _('Project will be published')

MSG_PIPELINE_NO_INPUT = _('Pipeline has no input')
MSG_PIPELINE_IN_KERNEL = _('Pipeline (as mapping set) is already published')
MSG_PIPELINE_NOT_IN_KERNEL = _('Pipeline (as mapping set) will be published')
MSG_PIPELINE_WRONG_PROJECT = _('Pipeline belongs to a different project in kernel')
MSG_PIPELINE_INPUT_CHANGED = _('Input data will be changed')
MSG_PIPELINE_SCHEMA_CHANGED = _('Schema data will be changed')

MSG_CONTRACT_READ_ONLY = _('Contract is read only')
MSG_CONTRACT_NO_ENTITIES = _('Contract has no entity types')
MSG_CONTRACT_NO_MAPPING_RULES = _('Contract has no mapping rules')
MSG_CONTRACT_MAPPING_RULES_ERROR = _('Contract mapping rules have errors')
MSG_CONTRACT_IN_KERNEL = _('Contract (as mapping) is already published')
MSG_CONTRACT_NOT_IN_KERNEL = _('Contract (as mapping) will be published')
MSG_CONTRACT_WRONG_MAPPINGSET = _('Contract belongs to a different pipeline (mapping set) in kernel')
MSG_CONTRACT_WRONG_PROJECT = _('Contract belongs to a different project in kernel')
MSG_CONTRACT_MAPPING_RULES_CHANGED = _('Mapping rules data will be changed')

MSG_ENTITY_IN_KERNEL_SCHEMA = _('Entity type "{}" (as schema) is already published')
MSG_ENTITY_NOT_IN_KERNEL_SCHEMA = _('Entity type "{}" (as schema) will be published')
MSG_ENTITY_SCHEMA_CHANGED = _('Entity type "{}" (as schema) data will be changed')

MSG_ENTITY_IN_KERNEL_PROJECT_SCHEMA = _('Entity type "{}" (as project schema) is already published')
MSG_ENTITY_NOT_IN_KERNEL_PROJECT_SCHEMA = _('Entity type "{}" (as project schema) will be published')
MSG_ENTITY_WRONG_PROJECT = _('Entity type "{}" (as project schema) belongs to a different project in kernel')


class PublishError(Exception):
    pass


def kernel_artefacts_to_ui_artefacts():
    '''
    Fetches all projects in kernel and all linked mappingsets and tranform them into pipelines,
    taking also the linked mappings+schemas and transform them into contracts.
    '''
    KERNEL_URL = utils.get_kernel_server_url()

    projects = utils.get_all_docs(f'{KERNEL_URL}/projects/')
    for kernel_project in projects:
        project_id = kernel_project['id']

        if not models.Project.objects.filter(pk=project_id).exists():
            # create the project
            models.Project.objects.create(project_id=project_id, name=kernel_project['name'])
        project = models.Project.objects.get(pk=project_id)

        # fetch linked mapping sets
        mappingsets = utils.get_all_docs(kernel_project['mappingset_url'])
        for mappingset in mappingsets:
            mappingset_id = mappingset['id']

            if not models.Pipeline.objects.filter(mappingset=mappingset_id).exists():
                # create the pipeline
                models.Pipeline.objects.create(
                    id=mappingset_id,  # use mappingset id as pipeline id
                    name=mappingset['name'],
                    schema=mappingset['schema'],
                    input=mappingset['input'],
                    mappingset=mappingset_id,
                    project=project,
                )
            pipeline = models.Pipeline.objects.get(mappingset=mappingset_id)

            # fetch linked mappings
            mappings = utils.get_all_docs(mappingset['mappings_url'])
            for mapping in mappings:
                mapping_id = mapping['id']

                if models.Contract.objects.filter(mapping=mapping_id).exists():
                    # do not update the current contract
                    continue

                ps_fields = 'id,schema,schema_definition'
                ps_url = mapping['projectschemas_url'] + f'&fields={ps_fields}'
                project_schemas = utils.get_all_docs(ps_url)

                # find out the linked schema ids from the project schema ids (mapping entities)
                entities = mapping['definition']['entities']              # format    {entity name: ps id}
                entity_names_by_id = {v: k for k, v in entities.items()}  # turn into {ps id: entity name}
                schemas = {
                    entity_names_by_id[ps['id']]: ps['schema']
                    for ps in project_schemas
                }

                models.Contract.objects.create(
                    id=mapping_id,  # use mapping id as contract id
                    name=mapping['name'],
                    pipeline=pipeline,

                    mapping_rules=[
                        {'id': str(uuid.uuid4()), 'source': rule[0], 'destination': rule[1]}
                        for rule in mapping['definition']['mapping']
                    ],
                    entity_types=[
                        ps['schema_definition']
                        for ps in project_schemas
                    ],

                    is_active=mapping['is_active'],
                    is_read_only=mapping['is_read_only'],

                    mapping=mapping_id,
                    kernel_refs={
                        # Refers to project schemas in Kernel {entity name: project schema id}
                        'entities': entities,
                        # Refers to schemas in Kernel {entity name: schema id}
                        'schemas': schemas,
                    },
                    published_on=mapping['modified'],
                )


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

    if not contract.pipeline.input or not contract.mapping_rules or not contract.entity_types:
        return [], []

    # check kernel connection
    if not utils.test_connection():
        return (
            [{'description': MSG_CONTRACT_VALIDATION_KERNEL_ERROR}],
            [],
        )

    # validate the mapping rules
    # -------------------------------------------------------
    # kernel is expecting a payload with this format:
    # {
    #    "submission_payload": { json sample },
    #    "mapping_definition": {
    #      "entities": {
    #        "entity-type-name-1": UUID,
    #        "entity-type-name-2": UUID,
    #        "entity-type-name-3": UUID,
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

    payload = {
        'submission_payload': contract.pipeline.input,
        'mapping_definition': {
            'entities': entities,
            'mapping': contract.kernel_rules,
        },
        'schemas': schemas,
    }

    resp = request(
        method='post',
        url=f'{utils.get_kernel_server_url()}/validate-mappings/',
        json=json.loads(json.dumps(payload)),
        headers=utils.get_auth_header(),
    )
    if resp.status_code == status.HTTP_200_OK:
        data = resp.json()
        errors = data.get('mapping_errors', [])
        output = data.get('entities', [])
        return (errors, output)
    # The 400 response we get from the rest-framework serializers is a
    # dictionary. The keys are the serializer field names and the values are
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
        description = MSG_CONTRACT_VALIDATION_ERROR.format(str(data))
        errors = [{'description': description}]
        return (errors, [])


def publish_project(project):
    '''
    Publish the project in Kernel (without linked data)
    '''

    pk = str(project.pk)
    artefacts = model_to_artefacts(project)

    try:
        kernel_data_request(f'projects/{pk}/artefacts/', 'patch', artefacts)
    except Exception as e:
        raise PublishError(e)


def publish_pipeline(pipeline):
    '''
    Transform pipeline to kernel artefacts and publish (without linked data)
    '''

    pk = str(pipeline.project.pk)

    # if there is at least one readonly contract do not update only create if missing
    action = 'create' if pipeline.contracts.filter(is_read_only=True).exists() else 'upsert'
    artefacts = model_to_artefacts(pipeline)
    mappingset_id = artefacts['mappingsets'][0]['id']

    data = {
        'action': action,
        **artefacts,
    }

    try:
        kernel_data_request(f'projects/{pk}/artefacts/', 'patch', data)
    except Exception as e:
        raise PublishError(e)

    # update pipeline
    pipeline.mappingset = mappingset_id
    pipeline.save()


def publish_contract(contract):
    '''
    Transform contract to kernel artefacts and publish
    '''

    status = publish_preflight(contract)
    if status.get('error'):
        raise PublishError(status['error'])

    artefacts = model_to_artefacts(contract)

    # Basic Kernel IDs
    pk = str(contract.pipeline.project.pk)
    mappingset_id = artefacts['mappingsets'][0]['id']
    mapping_id = artefacts['mappings'][0]['id']

    try:
        kernel_data_request(f'projects/{pk}/artefacts/', 'patch', artefacts)
    except Exception as e:
        raise PublishError(e)

    # update pipeline
    contract.pipeline.mappingset = mappingset_id
    contract.pipeline.save()

    # update contract
    contract.published_on = timezone.now()
    contract.mapping = mapping_id
    contract.kernel_refs = {
        'entities': artefacts['mappings'][0]['definition']['entities'],
        'schemas': {schema['name']: schema['id'] for schema in artefacts['schemas']},
    }
    contract.save()

    return {
        'artefacts': {
            'project': pk,
            'mappingset': mappingset_id,
            'mapping': mapping_id,
            **contract.kernel_refs
        }
    }


def publish_preflight(contract):
    '''
    Performs a check for possible contract publish consequences against kernel.


    Expected outcome by type:

    - Error (blockers, with any of them the contract cannot be published)

        - Pipeline has no input
        - Pipeline belongs to a different project in kernel
        - Contract is read only
        - Contract has no entity types
        - Contract has no mapping rules
        - Contract mapping rules have errors
        - Contract belongs to a different project in kernel
        - Contract belongs to a different pipeline (mapping set) in kernel
        - Entity type "XXX" (as project schema) belongs to a different project in kernel

    - Warning (warns if any of the artefacts is already published)

        - Project is already published
        - Pipeline (as mapping set) is already published
        - Contract (as mapping) is already published
        - Entity type "XXX" (as schema) is already published
        - Entity type "XXX" (as project schema) is already published

    - Info (informs about the publish effects)

        - Project will be published
        - Pipeline (as mapping set) will be published
        - Input data will be changed
        - Schema data will be changed
        - Contract (as mapping) will be published
        - Mapping rules data will be changed
        - Entity type "XXX" (as schema) will be published
        - Entity type "XXX" (as schema) data will be changed
        - Entity type "XXX" (as project schema) will be published

    '''

    def __get(model, pk):
        try:
            return kernel_data_request(f'{model}/{pk}/')
        except Exception:
            return None

    outcome = {
        'error': [],
        'warning': [],
        'info': [],
    }

    pipeline = contract.pipeline
    project = pipeline.project

    if not pipeline.input:
        outcome['error'].append(MSG_PIPELINE_NO_INPUT)
    if contract.is_read_only:
        outcome['error'].append(MSG_CONTRACT_READ_ONLY)
    if not contract.entity_types:
        outcome['error'].append(MSG_CONTRACT_NO_ENTITIES)
    if not contract.mapping_rules:
        outcome['error'].append(MSG_CONTRACT_NO_MAPPING_RULES)
    if contract.mapping_errors:
        outcome['error'].append(MSG_CONTRACT_MAPPING_RULES_ERROR)

    # 1. Check the project in Kernel
    kernel_project = __get('projects', project.project_id)
    if kernel_project:
        outcome['warning'].append(MSG_PROJECT_IN_KERNEL)
    else:
        outcome['info'].append(MSG_PROJECT_NOT_IN_KERNEL)

    # 2. Check the pipeline in Kernel (as mapping set)
    mappingset = None
    if pipeline.mappingset:
        mappingset = __get('mappingsets', pipeline.mappingset)
        if mappingset:
            outcome['warning'].append(MSG_PIPELINE_IN_KERNEL)

            # 2.1 Check linked project
            if mappingset['project'] != str(project.project_id):
                outcome['error'].append(MSG_PIPELINE_WRONG_PROJECT)

            # 2.2 Check data: input & schema
            if json.dumps(mappingset['input'], sort_keys=True) != json.dumps(pipeline.input, sort_keys=True):
                outcome['info'].append(MSG_PIPELINE_INPUT_CHANGED)
            if json.dumps(mappingset['schema'], sort_keys=True) != json.dumps(pipeline.schema, sort_keys=True):
                outcome['info'].append(MSG_PIPELINE_SCHEMA_CHANGED)
    if not mappingset:
        outcome['info'].append(MSG_PIPELINE_NOT_IN_KERNEL)

    # 3. Check the contract in Kernel (as mapping)
    mapping = None
    if contract.mapping:
        mapping = __get('mappings', contract.mapping)
        if mapping:
            outcome['warning'].append(MSG_CONTRACT_IN_KERNEL)

            # 3.1 Check linked project
            if mapping['project'] != str(project.project_id):
                outcome['error'].append(MSG_CONTRACT_WRONG_PROJECT)

            #  3.2 Check linked mapping set
            if mapping['mappingset'] != str(pipeline.mappingset):
                outcome['error'].append(MSG_CONTRACT_WRONG_MAPPINGSET)

            # 3.3 Check mapping rules
            kernel_rules = mapping['definition']['mapping']
            ui_rules = contract.kernel_rules
            if len(kernel_rules) != len(ui_rules):
                outcome['info'].append(MSG_CONTRACT_MAPPING_RULES_CHANGED)
            else:
                for i in range(len(kernel_rules)):
                    if kernel_rules[i][0] != ui_rules[i][0] or kernel_rules[i][1] != ui_rules[i][1]:
                        outcome['info'].append(MSG_CONTRACT_MAPPING_RULES_CHANGED)
                        break
    if not mapping:
        outcome['info'].append(MSG_CONTRACT_NOT_IN_KERNEL)

    # 4. Check the contract entity types in Kernel (as schemas and project schemas)
    kernel_refs = contract.kernel_refs if contract.kernel_refs else {}
    if contract.entity_types:
        for entity in contract.entity_types:
            name = entity['name']
            schema = None
            ps = None

            # 4.1 Check as schema
            schema_id = kernel_refs.get('schemas', {}).get(name)
            if schema_id:
                schema = __get('schemas', schema_id)
                if schema:
                    outcome['warning'].append(MSG_ENTITY_IN_KERNEL_SCHEMA.format(name))

                    # 4.1.1 Check schema definition
                    if json.dumps(schema['definition'], sort_keys=True) != json.dumps(entity, sort_keys=True):
                        outcome['info'].append(MSG_ENTITY_SCHEMA_CHANGED.format(name))
            if not schema:
                outcome['info'].append(MSG_ENTITY_NOT_IN_KERNEL_SCHEMA.format(name))

            # 4.2 Check as project schema
            ps_id = kernel_refs.get('entities', {}).get(name)
            if ps_id:
                ps = __get('projectschemas', ps_id)
                if ps:
                    outcome['warning'].append(MSG_ENTITY_IN_KERNEL_PROJECT_SCHEMA.format(name))
                    # 4.2.1 Check linked project
                    if ps['project'] != str(project.project_id):
                        outcome['error'].append(MSG_ENTITY_WRONG_PROJECT.format(name))
            if not ps:
                outcome['info'].append(MSG_ENTITY_NOT_IN_KERNEL_PROJECT_SCHEMA.format(name))

    return outcome


################################################################################
# HELPERS
################################################################################

def model_to_artefacts(instance):
    if isinstance(instance, models.Project):
        return {'name': instance.name}

    if isinstance(instance, models.Pipeline):
        project_artefacts = model_to_artefacts(instance.project)
        mappingset_id = str(instance.mappingset or uuid.uuid4())

        return {
            **project_artefacts,

            # the pipelines have a 1:1 relationship with kernel mappingsets
            'mappingsets': [{
                'id': mappingset_id,
                'name': instance.name,
                'input': instance.input,
                'schema': instance.schema,
            }],
        }

    pipeline_artefacts = model_to_artefacts(instance.pipeline)
    mappingset_id = pipeline_artefacts['mappingsets'][0]['id']

    mapping_id = str(instance.mapping or uuid.uuid4())

    if not instance.kernel_refs:
        instance.kernel_refs = {}
    schema_ids = instance.kernel_refs.get('schemas', {})
    entity_ids = instance.kernel_refs.get('entities', {})

    # build schemas/project schemas from contract entities, include a new id if missing
    schemas = []
    entities = {}
    for entity_type in instance.entity_types:
        name = entity_type['name']
        schema = {
            'id': schema_ids.get(name, str(uuid.uuid4())),
            'name': name,
            'definition': entity_type,
        }
        schemas.append(schema)
        entities[name] = entity_ids.get(name, schema['id'])

    return {
        **pipeline_artefacts,

        # the contract entity types correspond to kernel schemas
        'schemas': schemas,

        # the contracts have a 1:1 relationship with kernel mappings
        'mappings': [{
            'id': mapping_id,
            'name': instance.name,
            'definition': {
                # the contract mapping_rules property corresponds
                # to definition mapping but with different rules format
                'mapping': instance.kernel_rules,
                'entities': entities,
            },
            'mappingset': mappingset_id,
            'is_active': True,
            'is_ready_only': instance.is_read_only,
        }],
    }


def kernel_data_request(url='', method='get', data=None):
    '''
    Handle requests to the kernel server
    '''

    res = request(
        method=method,
        url=f'{utils.get_kernel_server_url()}/{url}',
        json=data or {},
        headers=utils.get_auth_header(),
    )

    res.raise_for_status()

    if res.status_code == status.HTTP_204_NO_CONTENT:
        return None
    return json.loads(res.content.decode('utf-8'))
