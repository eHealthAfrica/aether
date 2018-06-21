import json
import requests
import ast
import uuid
import os

from aether.common.kernel import utils

from . import models


def validate_pipeline(pipeline):
    '''
    Call kernel to check if the pipeline is valid and return the errors and
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

    if not pipeline.input or not pipeline.mapping or not pipeline.entity_types:
        return [], []

    # check kernel connection
    kong_apikey = os.environ.get('KONG_APIKEY', '')
    if not utils.test_connection(kong_apikey):
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
        response = kernel_data_request('validate-mappings/', 'post', json.loads(json.dumps(payload)))

        return (
            response['mapping_errors'] if 'mapping_errors' in response else [],
            response['entities'] if 'entities' in response else [],
        )

    except Exception as e:
        return (
            [{'description': f'It was not possible to validate the pipeline: {str(e)}'}],
            []
        )


def kernel_data_request(url='', method='get', data=None):
    '''
    Handle requests to the kernel server
    '''
    if data is None:
        data = {}
    kernerl_url = utils.get_kernel_server_url()
    kong_apikey = os.environ.get('KONG_APIKEY', '')
    res = requests.request(method=method,
                        url=f'{kernerl_url}/{url}',
                        headers=utils.get_auth_header(kong_apikey),
                        json=data
                        )
    if res.status_code >= 200 and res.status_code < 400:
        try:
            return res.json()
        except Exception:
            return res
    else:
        try:
            error = json.loads(res.content)
        except Exception:
            error = res.content
        raise Exception(error)


def create_new_kernel_object(object_name, pipeline, data, project_name='Aux', entity_name=None):
    try:
        res = kernel_data_request(f'{object_name.lower()}s/', 'post', data)
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
    return pipeline


def update_kernel_object(object_name, id, data):
    return kernel_data_request(f'{object_name.lower()}s/{id}/', 'put', data)


def is_object_linked(kernel_refs, object_name, entity_type_name=''):
    if kernel_refs and object_name in kernel_refs:
        try:
            if object_name is 'schema' or object_name is 'projectSchema':
                if entity_type_name in kernel_refs[object_name]:
                    url = f'{object_name.lower()}s/{kernel_refs[object_name][entity_type_name]}'
                else:
                    return False
            else:
                url = f'{object_name.lower()}s/{kernel_refs[object_name]}/'
            kernel_data_request(url, 'get')
            return True
        except Exception:
            return False
    else:
        return False


def create_project_schema_object(name, pipeline, schema_id, entity_name):
    if not is_object_linked(pipeline.kernel_refs, 'projectSchema', entity_name):
        project_schema_data = {
                            'name': name,
                            'mandatory_fields': '[]',
                            'transport_rule': '[]',
                            'masked_fields': '[]',
                            'is_encrypted': False,
                            'project': pipeline.kernel_refs['project'],
                            'schema': schema_id
                        }
        create_new_kernel_object('projectSchema',
                                 pipeline, project_schema_data, entity_name=entity_name)
    return pipeline


def publish_preflight(pipeline, project_name, outcome):
    '''
    Performs a check for possible pipeline publish errors against kernel
    '''
    if pipeline.mapping_errors:
        outcome['error'].append('Mappings have errors')
        return outcome
    for entity_type in pipeline.entity_types:
        if is_object_linked(pipeline.kernel_refs, 'schema', entity_type['name']):
            outcome['exists'].append({entity_type['name']: '{} schema with id {} exists'.format(
                                        entity_type['name'],
                                        pipeline.kernel_refs['schema'][entity_type['name']])})
        else:
            get_by_name = kernel_data_request(f'schemas/?name={entity_type["name"]}')['results']
            if len(get_by_name):
                outcome['exists'].append({entity_type['name']: 'Schema with name {} exists on kernel'.format(
                                        entity_type['name'])})
        if not is_object_linked(pipeline.kernel_refs, 'projectSchema', entity_type['name']):
            get_by_name = kernel_data_request('projectschemas/?name={}-{}'.format(
                                              project_name, entity_type['name']))['results']
            if len(get_by_name):
                project_schema_name = '{}-{}'.format(project_name, entity_type['name'])
                outcome['exists'].append({project_schema_name: 'Project schema {} exists on kernel'.format(
                                        project_schema_name)})
    if is_object_linked(pipeline.kernel_refs, 'mapping'):
        outcome['exists'].append({pipeline.name: 'Mapping with id {} exists'.format(
                                        pipeline.kernel_refs['mapping'])})
    else:
        get_by_name = kernel_data_request(f'mappings/?name={pipeline.name}')['results']
        if len(get_by_name):
            outcome['exists'].append({pipeline.name: 'Pipeline (mapping) with name {} exists on kernel.'.format(
                                    pipeline.name)})
    return outcome


def publish_pipeline(pipeline, projectname, overwrite=False):
    '''
    Transform pipeline to kernel data and publish
    '''
    outcome = {
        'successful': [],
        'error': [],
        'exists': []
    }
    pipeline.kernel_refs = pipeline.kernel_refs if pipeline.kernel_refs else {}
    project_data = {
        'revision': str(uuid.uuid4()),
        'name': projectname,
        'salad_schema': '[]',
        'jsonld_context': '[]',
        'rdf_definition': '[]'
    }
    try:
        create_new_kernel_object('project', pipeline, project_data)
        outcome['successful'].append('{} project created'.format(projectname))
    except Exception:
        if overwrite and 'project' in pipeline.kernel_refs:
            update_kernel_object('project', pipeline.kernel_refs['project'], project_data)
            outcome['successful'].append('{} project updated'.format(projectname))
        else:
            get_by_name = kernel_data_request(f'projects/?name={projectname}')['results'][0]
            pipeline.kernel_refs['project'] = get_by_name['id']
            outcome['successful'].append('Existing {} project used'.format(projectname))

    for entity_type in pipeline.entity_types:
        schema_name = entity_type['name']
        schema_data = {
            'revision': str(uuid.uuid4()),
            'name': schema_name,
            'type': entity_type['type'],
            'definition': entity_type
        }
        try:
            create_new_kernel_object('schema', pipeline, schema_data, projectname)
            outcome['successful'].append('{} schema created'.format(
                entity_type['name']))
        except Exception as e:
            if overwrite:
                outcome = overwrite_kernel_schema(pipeline, schema_name, schema_data, projectname, outcome)
            else:
                outcome['error'].append(str(e))

    mapping = [
        [rule['source'], rule['destination']]
        for rule in pipeline.mapping
    ]
    mapping_data = {
        'name': pipeline.name,
        'definition': {
            'entities': pipeline.kernel_refs.get('projectSchema', {}),
            'mapping': mapping
            },
        'revision': str(uuid.uuid4()),
        'project': pipeline.kernel_refs['project']
    }
    try:
        create_new_kernel_object('mapping', pipeline, mapping_data, projectname)
        outcome['successful'].append('{} mapping created'.format(mapping_data['name']))
    except Exception as e:
        if overwrite and 'mapping' in pipeline.kernel_refs:
            update_kernel_object('mapping', pipeline.kernel_refs['mapping'], mapping_data)
            outcome['successful'].append('{} mapping updated'.format(pipeline.name))
        else:
            outcome['error'].append(str(e))
    return outcome


def overwrite_kernel_schema(pipeline, schema_name, schema_data, projectname, outcome):
    is_schema_linked = is_object_linked(pipeline.kernel_refs, 'schema', schema_name)
    is_project_schema_linked = is_object_linked(pipeline.kernel_refs, 'projectSchema', schema_name)

    if is_schema_linked:
        update_kernel_object('schema', pipeline.kernel_refs['schema'][schema_name], schema_data)
    else:
        pipeline.kernel_refs['schema'] = {} if 'schema' not in pipeline.kernel_refs \
            else pipeline.kernel_refs['schema']
        get_by_name = kernel_data_request(f'schemas/?name={schema_name}')['results'][0]
        update_kernel_object('schema', get_by_name['id'], schema_data)
        pipeline.kernel_refs['schema'][schema_name] = get_by_name['id']
    outcome['successful'].append('{} schema updated'.format(schema_name))

    project_schema_name = '{}-{}'.format(projectname, schema_name)
    project_schema_data = {
        'name': project_schema_name,
        'mandatory_fields': '[]',
        'transport_rule': '[]',
        'masked_fields': '[]',
        'is_encrypted': False,
        'project': pipeline.kernel_refs['project'],
        'schema': pipeline.kernel_refs['schema'][schema_name]
    }

    if is_project_schema_linked:
        update_kernel_object('projectSchema',
                             pipeline.kernel_refs['projectSchema'][schema_name],
                             project_schema_data)
    else:
        pipeline.kernel_refs['projectSchema'] = {} if 'projectSchema' not in pipeline.kernel_refs \
            else pipeline.kernel_refs['projectSchema']
        get_by_name = kernel_data_request(f'projectschemas/?name={project_schema_name}')['results'][0]
        update_kernel_object('projectSchema',
                             get_by_name['id'],
                             project_schema_data)
        pipeline.kernel_refs['projectSchema'][schema_name] = get_by_name['id']
    outcome['successful'].append('{}-{} project schema updated'.format(projectname, schema_name))
    return outcome


def is_linked_to_pipeline(object_name, id):
    kwargs = {
        '{0}__{1}'.format('kernel_refs', object_name): id
    }
    linked_pipeline = models.Pipeline.objects.filter(**kwargs)
    return True if len(linked_pipeline) else False


def convert_mappings(mapping_from_kernel):
    return [
        {'source': mapping[0], 'destination': mapping[1]}
        for mapping in mapping_from_kernel
    ]


def convert_entity_types(entities_from_kernel):
    result = {'schemas': [], 'ids': {}}
    for entity, entity_id in entities_from_kernel.items():
        project_schema = kernel_data_request(f'projectschemas/{entity_id}/')
        schema = kernel_data_request(f'schemas/{project_schema["schema"]}/')
        result['schemas'].append(schema['definition'])
        result['ids'][schema['name']] = schema['id']
    return result


def create_new_pipeline_from_kernel(kernel_object):
    entity_types = convert_entity_types(kernel_object['definition']['entities'])
    new_pipeline = models.Pipeline.objects.create(
        name=kernel_object['name'],
        mapping=convert_mappings(kernel_object['definition']['mapping']),
        entity_types=entity_types['schemas'],
        kernel_refs={
            'project': kernel_object['project'],
            'schema': entity_types['ids'],
            'projectschema': kernel_object['definition']['entities'],
            'mapping': kernel_object['id']
        }
    )
    return new_pipeline


def kernel_to_pipeline():
    try:
        mappings = kernel_data_request('mappings/')['results']
        pipelines = []
        for mapping in mappings:
            if not is_linked_to_pipeline('mapping', mapping['id']):
                pipelines.append(create_new_pipeline_from_kernel(mapping))
        return pipelines
    except Exception as e:
        raise e
