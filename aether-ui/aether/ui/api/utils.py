import json
import requests
import ast
import uuid
import avro.schema

from aether.common.kernel import utils
from django.http import JsonResponse
from jsonpath_ng import jsonpath, parse

from . import models


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

def kernel_data_request(url='', method='get', data={}):
    '''
    Handle requests to the kernel server
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


def publishPipeline(pipelineid, projectname):
    '''
    Transform pipeline to kernel data and publish
    '''
    outcome = {
        'successful': [],
        'failed': [],
        'exists': []
    }
    try:
        pipeline = models.Pipeline.objects.get(pk=pipelineid)
        if pipeline.mapping_errors:
            outcome['failed'].append({'message': 'Mappings have errors', 'status': 'Bad Request'})
            return JsonResponse({'links': None, 'info': outcome}, status=400)
        else:
            project_data = {
                'revision': str(uuid.uuid4()),
                'name': '{}'.format(projectname),
                'salad_schema': '[]',
                'jsonld_context': '[]',
                'rdf_definition': '[]'
            }

            # check if pipeline references existing kernel records (update if exists)
            if not is_object_linked(pipeline.kernel_refs, 'project'):
                create_new_kernel_object('project', pipeline, project_data, projectname)
                outcome['successful'].append({'message': '{} project created'.format(projectname),
                                             'status': 'Ok'})

            for entity_type in pipeline.entity_types:
                schema_data = {
                    'revision': str(uuid.uuid4()),
                    'name': entity_type['name'],
                    'type': entity_type['type'],
                    'definition': entity_type
                }
                if is_object_linked(pipeline.kernel_refs, 'schema', entity_type['name']):
                    # Notify user of existing object, and confirm override
                    outcome['exists'].append(
                                            {'message': '{} schema with id {} exists'.format(
                                                entity_type['name'],
                                                pipeline.kernel_refs['schema'][entity_type['name']]),
                                                'status': 'Ok'}
                                            )
                else:
                    try:
                        create_new_kernel_object('schema', pipeline, schema_data, projectname)
                        outcome['successful'].append({'message': '{} schema created'.format(
                            entity_type['name']), 'status': 'Ok'})
                    except Exception as e:
                        outcome['failed'].append({'message': str(e), 'status': 'Bad Request'})

            if not len(outcome['failed']) and not len(outcome['exists']):
                mapping = [
                    [rule['source'], rule['destination']]
                    for rule in pipeline.mapping
                ]
                mapping_data = {
                    'name': pipeline.name,
                    'definition': {
                        'entities': pipeline.kernel_refs['projectSchema'],
                        'mapping': mapping
                        },
                    'revision': str(uuid.uuid4()),
                    'project': pipeline.kernel_refs['project']
                }
                if is_object_linked(pipeline.kernel_refs, 'mapping'):
                    # Notify user of existing object, and confirm override
                    outcome['exists'].append({'message': 'Mapping with id {} exists'.format(
                                        pipeline.kernel_refs['mapping']), 'error': ''})
                else:
                    create_new_kernel_object('mapping', pipeline, mapping_data, projectname)
                    outcome['successful'].append({'message': '{} mapping created'.format(mapping_data['name']),
                                                 'status': 'Ok'})

            return JsonResponse({'links': pipeline.kernel_refs, 'info': outcome},
                                status=200)
    except Exception as e:
        outcome['failed'].append({'message': str(e), 'status': 'Bad request'})
        return JsonResponse({'links': None, 'info': outcome}, status=400)

def is_linked_to_pipeline(object_name, id):
    kwargs = {
        '{0}__{1}'.format('kernel_refs', object_name): id
    }
    linked_pipeline = models.Pipeline.objects.filter(**kwargs)
    return True if len(linked_pipeline) else False

def convertMappings(mapping_from_kernel):
    result = []
    for mapping in mapping_from_kernel:
        result.append({'source': mapping[0], 'destination': mapping[1]})
    return result

def convertEntityTypes(entities_from_kernel):
    result = []
    for entity in entities_from_kernel:
        print(entities_from_kernel[entity])
        project_schema = kernel_data_request(f'projectschemas/{entities_from_kernel[entity]}')
        schema = kernel_data_request(f'schemas/{project_schema["schema"]}')
        result.append(schema['definition'])
    return result

def generate_sample_input_from_mapping(mappings, schemas):
    input_data_object = {}

    def create_object_from_property_list(property_list, obj={}, property_type='dict'):
        property_name = property_list.pop(0)
        if len(property_list):
            if property_name not in obj:
                obj[property_name] = {}
            return create_object_from_property_list(property_list, obj[property_name], property_type)
        else:
            if property_type is 'int':
                obj[property_name] = 1
            elif property_type is 'bool':
                obj[property_name] = True
            elif property_type is 'list':
                obj[property_name] = []
            elif property_type is 'dict':
                obj[property_name] = {}
            elif property_type is 'tuple':
                obj[property_name] = (0, 1)
            elif property_type is 'float':
                obj[property_name] = 0.1
            else:
                obj[property_name] = 'a'
        return obj

    for mapping in mappings:
        source = mapping[0].split('.')
        destination_entity = mapping[1].split('.')[0]
        print('Schemas', schemas)
        print('Des Entity', destination_entity)
        create_object_from_property_list(source, input_data_object)
    return input_data_object
        

def create_new_pipeline_from_kernel(entry, kernel_object):
    if entry is 'mapping':
        entity_types = convertEntityTypes(kernel_object['definition']['entities'])
        models.Pipeline.create(
            name=kernel_object['name'],
            input=generate_sample_input_from_mapping(kernel_object['definition']['mapping'],
                                                     entity_types),
            entity_types=entity_types,
            mapping=convertMappings(kernel_object['definition']),
            # kernel_refs=PIPELINE_EXAMPLE_1['kernel_refs']
        )

def generate_sample_schema_data(schemas):
    results = {}
    for schema in schemas:
        c = avro.schema.Parse(json.dumps(schema))
        print(c.fields)
    return results    

def kernel_to_pipeline():
    mappings = kernel_data_request('mappings')['results']
    for mapping in mappings:
        if not is_linked_to_pipeline('mapping', mapping['id']):
            create_new_pipeline_from_kernel('mapping', mapping)
    entity_types = convertEntityTypes(mappings[0]['definition']['entities'])
    sample_schema_data = generate_sample_schema_data(entity_types)
    x = generate_sample_input_from_mapping(mappings[0]['definition']['mapping'], entity_types)
    print('YUEO', x)
    return []
