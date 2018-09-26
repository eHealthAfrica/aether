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

import collections
import json
import logging
import re
import string
import uuid

import jsonpath_ng
from spavro.schema import parse as parse_schema
from spavro.io import validate

from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer
from pygments.lexers.python import Python3Lexer

from . import models, constants, avro_tools


logger = logging.getLogger('django')


class CachedParser(object):
    # jsonpath_ng.parse is a very time/compute expensive operation. The output is always
    # the same for a given path. To reduce the number of times parse() is called, we cache
    # all calls to jsonpath_ng here. This greatly improves extraction performance. However,
    # when run in an instance of Django with debug=True, Django's db call caching causes massive
    # memory usage. In debug, we must periodically call db.reset_queries() to avoid unbounded
    # memory expansion. If you run this with DEBUG = true, you'll eventually go OOM from the
    # memory leak.

    cache = {}

    @staticmethod
    def parse(path):
        # we never need to call parse directly; use find()
        if path not in CachedParser.cache.keys():
            CachedParser.cache[path] = jsonpath_ng.parse(path)
        return CachedParser.cache[path]

    @staticmethod
    def find(path, obj):
        # find is an optimized call with a potentially cached parse object.
        parser = CachedParser.parse(path)
        return parser.find(obj)


class EntityValidationError(Exception):
    pass


Entity = collections.namedtuple(
    'Entity',
    ['payload', 'projectschema_name', 'status'],
)

EntityValidationResult = collections.namedtuple(
    'EntityValidationResult',
    ['validation_errors', 'entities'],
)


def __prettified__(response, lexer):
    # Truncate the data. Alter as needed
    response = response[:5000]
    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')
    # Highlight the data
    response = highlight(response, lexer, formatter)
    # Get the stylesheet
    style = '<style>' + formatter.get_style_defs() + '</style>'
    # Safe the output
    return mark_safe(style + response)


def json_prettified(value, indent=2):
    '''
    Function to display pretty version of our json data
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    '''
    return __prettified__(json.dumps(value, sort_keys=True, indent=indent), JsonLexer())


def code_prettified(value):
    '''
    Function to display pretty version of our code data
    '''
    return __prettified__(value, Python3Lexer())


def json_printable(obj):
    # Note: a combinations of JSONB in postgres and json parsing gives a nasty db error
    # See: https://bugs.python.org/issue10976#msg159391
    # and
    # http://www.postgresql.org/message-id/E1YHHV8-00032A-Em@gemulon.postgresql.org
    if isinstance(obj, dict):
        return {json_printable(k): json_printable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_printable(elem) for elem in obj]
    elif isinstance(obj, str):
        # Only printables
        return ''.join(x for x in obj if x in string.printable)
    else:
        return obj


custom_jsonpath_wildcard_regex = re.compile(
    '(\$\.)*([a-zA-Z0-9_-]+\.)*?[a-zA-Z0-9_-]+\*')
incomplete_json_path_regex = re.compile('[a-zA-Z0-9_-]+\*')


def find_by_jsonpath(obj, path):
    '''
    This function wraps `jsonpath_ng.parse()` and
    `jsonpath_ng.jsonpath.Child.find()` in order to provide custom
    functionality as described in https://jira.ehealthafrica.org/browse/AET-38.

    If the any single element in `path` is a wildcard match prefixed by an arbitrary
    string, `find` will attempt to filter the results by that prefix. We then replace
    that section of the path with a single wildcard which becomes a valid jsonpath.
    We filter matches on their adherence to the partial path.

    **NOTE**: this behavior is not part of jsonpath spec.
    '''

    # Matches any string/jsonpath which starts with a sequence of characters
    # followed by an asterisk.
    match = custom_jsonpath_wildcard_regex.match(path)
    if match:
        # If `path` matches our criteria for a custom jsonpath, split `path` in
        # two parts based on the span of the regex.
        #
        # Example: given a `path` like `dose-*.id`, this will result in:
        #
        #     prefix = 'dose-'
        #     standard_jsonpath = '*.id'

        split_pos = match.end() - 1
        prefix = path[:split_pos].replace('$.', '')
        illegal = incomplete_json_path_regex.search(path)
        standard_jsonpath = path[:illegal.start()] + '*' + path[illegal.end():]

        # Perform an standard jsonpath search.
        result = []
        matches = CachedParser.find(standard_jsonpath, obj)
        for item in matches:
            full_path = str(item.full_path)
            # Only include item if its full path starts with `prefix`.
            if full_path.startswith(prefix):
                result.append(item)
        return result
    else:
        # Otherwise, perform a standard jsonpath search of `obj`.
        matches = CachedParser.find(path, obj)
        return matches


def get_field_mappings(mapping_definition):
    matches = find_by_jsonpath(mapping_definition, 'mapping[*]')
    mappings = [match.value for match in matches]
    return mappings


def JSP_get_basic_fields(avro_obj):
    return [match.value for match in find_by_jsonpath(avro_obj, 'fields[*].name')]


def get_entity_definitions(mapping_definition, schemas):
    required_entities = {}
    found_entities = find_by_jsonpath(mapping_definition, 'entities[*]')
    entities = [match.value for match in found_entities][0]
    for entity_definition in entities.items():
        entity_type, file_name = entity_definition
        required_entities[entity_type] = JSP_get_basic_fields(
            schemas.get(entity_type))
    return required_entities


def get_entity_requirements(entities, field_mappings):
    all_requirements = {}
    for entity_type, entity_definition in entities.items():
        entity_requirements = {}
        # find mappings that start with the entity name
        # and return a list with the entity_type ( and dot ) removed from the destination
        matching_mappings = [[src, dst.split(entity_type+'.')[1]]
                             for src, dst in field_mappings
                             if dst.startswith(entity_type+'.')]
        for field in entity_definition:
            # filter again to find sources pertaining to this particular field in this entity
            field_sources = [src for src,
                             dst in matching_mappings if dst == field]
            entity_requirements[field] = field_sources
        all_requirements[entity_type] = entity_requirements
    return all_requirements


def get_entity_stub(requirements, entity_definitions, entity_name, source_data):
    # takes an entity definition and returns an empty "stub" instance to be populated
    # copy an empty instance of available fields
    entity_stub = {k: [] for k in entity_definitions.get(entity_name)}
    # do a quick first resolution of paths to size output requirement
    for field, paths in requirements.get(entity_name).items():
        for i, path in enumerate(paths):
            # if this is a json path, we'll resolve it to see how big the result is
            if '#!' not in path:
                matches = find_by_jsonpath(source_data, path)
                [entity_stub[field].append(match.value) for match in matches]
            else:
                entity_stub[field].append(path)
    return entity_stub


class DeferrableAction(object):
    '''
    There are many potential race conditions that mapping creators shouldn't
    have to worry about. If something can't be resolved, we save it for later
    and attempt resolution at the end of entity construction.
    '''

    def __init__(self, path, args, function=None):
        self.res = None
        self.path = path
        self.func = function
        self.args = args
        self.complete = False
        self.error = None

    def run(self):
        self.error = None
        try:
            if not self.func:
                self.res = self.args
            else:
                self.res = self.func(*self.args)
            self.complete = True
        except Exception as e:
            self.complete = False
            self.error = e

    def resolve(self, entities):
        # Takes the entities object as an argument and attempts to assign the
        # resolved value to the proper path.
        p = self.path
        entities[p[0]][p[1]][p[2]] = self.res
        '''
        for loc in self.path:
            obj = obj[loc]
            if loc == self.path[-1]:
                obj.set(self.res)
        '''


def action_none():
    # Called via #!none acts as a dummy instruction when you need to terminate
    # a previously called instruction. For example:
    # ["hoh_firstname","Person.firstName"] -- if hoh_firstname is one value, all
    # subsequent instances of Person would receive that value. If we issue
    # ["#!none","Person.firstName"] after the first instruction, only the first
    # Person will receive that value as their firstName. All 2 -> n will get no value.
    return None


constant_type_coercions = {
    'int': lambda x: int(x),
    'boolean': lambda x: bool(x),
    'string': lambda x: str(x),
    'float': lambda x: float(x),
    'json': lambda x: json.loads(x)
}


def coerce(v, _type='string'):
    # Takes a value and tries to cast it to _type.
    # Optionally can parse JSON.
    try:
        fn = constant_type_coercions[_type]
    except KeyError:
        raise ValueError('%s not in available types for constants, %s' %
                         (_type, [i for i in constant_type_coercions.keys()],))
    try:
        return fn(v)
    except ValueError as err:
        raise ValueError('value: %s could not be coerced to type %s' % (v, _type))


def action_constant(args):
    # Called via #!constant#args returns the arguments to be assigned as the
    # value for the path WHERE:
    # args[0] is the value to be used as the constant AND
    # args[1] is the optional type of the output.
    try:
        _type = args[1]
    except IndexError:
        _type = 'string'
    return coerce(args[0], _type)


def object_contains(test, obj):
    # Recursive object comparison function.
    if obj == test:
        return True
    if isinstance(obj, list):
        return True in [object_contains(test, i) for i in obj]
    elif isinstance(obj, dict):
        return True in [object_contains(test, i) for i in obj.values()]
    return False


def anchor_reference(source, context, source_data, instance_number):
    # Anchors entity-referenced object to a context. See resolve_entity_reference
    try:
        this_obj = None
        obj_matches = find_by_jsonpath(source_data, source)
        if len(obj_matches) >= instance_number:
            this_obj = obj_matches[instance_number].value
        else:
            raise ValueError('source: %s unresolved' % (source))
        obj_matches = find_by_jsonpath(source_data, context)
        if not obj_matches:
            raise ValueError('context: %s unresolved' % (context))
        for idx, match in enumerate(obj_matches):
            if object_contains(this_obj, match.value):
                return idx
        raise ValueError('Object match not found in context')
    except Exception as err:
        logger.error(err)
        return -1


def resolve_entity_reference(
        args,
        constructed_entities,
        entity_type,
        field_name,
        instance_number,
        source_data,
):
    # Called via #!entity-reference#jsonpath looks inside of the entities to be
    # exported as currently constructed returns the value(s) found at
    # entity_jsonpath
    entity_jsonpath = args[0]
    matches = find_by_jsonpath(constructed_entities, entity_jsonpath)
    # optionally you can bind an element to a parent context.
    # For example you have an array of houses of unknown length, and each house has
    # a number of people. In the person record, you want to have a reference to House.id
    # which is generated for the house. In that case, our command might be:
    # #!entity-reference#House[*].id#house[*].person[*]#house[*]
    # I.E. (the_value_you_want, a_reference_object, a_parent_context)
    if len(args) == 3:
        source = args[1]
        context = args[2]
        idx = anchor_reference(source, context, source_data, instance_number)
        if idx >= 0:
            return matches[idx].value
    if len(matches) < 1:
        raise ValueError('path %s has no matches; aborting' % entity_jsonpath)
    if len(matches) < 2:
        # single value
        return matches[0].value
    else:
        # multiple values, attempt to choose the one aligned with this entity (#i)
        return matches[instance_number].value


def resolve_source_reference(path, entities, entity_name, i, field, data):
    # called via normal jsonpath as source
    # is NOT defferable as all source data should be present at extractor start
    # assignes values directly to entities within function and return new offset value (i)
    matches = find_by_jsonpath(data, path)
    if not matches:
        entities[entity_name][i][field] = None
        i += 1
    elif len(matches) == 1:
        # single value
        entities[entity_name][i][field] = matches[0].value
        i += 1
    else:
        for x, match in enumerate(matches):
            # multiple values, choose the one aligned with this entity (#i) & order of match(x)
            entities[entity_name][i][field] = matches[x].value
            i += 1
    return i


def get_or_make_uuid(entity_type, field_name, instance_number, source_data):
    # Either uses a pre-created uuid present in source_data --or-- creates a new
    # uuid and saves it in source data make one uuid, we may not use it
    value = str(uuid.uuid4())
    base = 'aether_extractor_enrichment'
    if source_data.get(base, {}).get(entity_type, {}).get(field_name):
        try:
            value = source_data.get(base, {}).get(
                entity_type).get(field_name)[instance_number]
        except IndexError as e:
            source_data[base][entity_type][field_name].append(value)
        finally:
            return value
    else:
        # create as little as the heirarchy as required
        # there's a better way to do this with collections.defaultdict
        if not source_data.get(base):
            source_data[base] = {}
        if not source_data[base].get(entity_type):
            source_data[base][entity_type] = {}
        if not source_data[base][entity_type].get(field_name):
            source_data[base][entity_type][field_name] = [value]
        else:
            source_data[base][entity_type][field_name].append(value)
        return value


def resolve_action(source_path):
    # Take a path instruction (like #!uuid# or #!entity-reference#a.json[path])
    # and resolves the action and arguments
    opts = source_path.split('#!')[1].split('#')
    # Action string is between #! and #
    action = opts[0]
    # If arguments are present we'll try and parse them
    args = opts[1:] if len(opts) > 1 else None
    return action, args


def extractor_action(
        source_path,
        constructed_entities,
        entity_type,
        field_name,
        instance_number,
        source_data,
):
    # Takes an extractor action instruction (#!action#args) and dispatches it to
    # the proper function
    action, args = resolve_action(source_path)
    logger.debug('extractor_action: fn %s; args %s' % (action, (args,)))
    if action == 'uuid':
        return get_or_make_uuid(entity_type, field_name, instance_number, source_data)
    elif action == 'entity-reference':
        return resolve_entity_reference(
            args,
            constructed_entities,
            entity_type,
            field_name,
            instance_number,
            source_data,
        )
    elif action == 'none':
        return action_none()
    elif action == 'constant':
        return action_constant(args)
    else:
        raise ValueError('No action with name %s' % action)


def extract_entity(entity_type, entities, requirements, data, entity_stub):
    failed_actions = []
    # calculate how many instances we need to split the resolved data
    # into by maximum number of path resolutions
    count = max([len(entity_stub.get(field)) for field in entity_stub.keys()])
    # make empty stubs for our expected outputs. One for each member
    # identified in count process
    entities[entity_type] = [
        {field: None for field in entity_stub.keys()} for i in range(count)]

    # iterate required fields, resolve paths and copy data to stubs
    for field, paths in requirements.get(entity_type).items():
        # ignore fields with empty paths
        if len(paths) < 1:
            for i in range(count):
                del entities[entity_type][i][field]
            continue
        # iterate over expected output entities
        # some paths will satisfy more than one entity, so we increment in different places
        i = 0
        while i <= count-1:
            # if fewer paths than required use the last value
            # otherwise use the current path
            path = paths[-1] if len(paths) < (i + 1) else paths[i]
            # check to see if we need to use a special reference here
            if '#!' not in path:
                i = resolve_source_reference(
                    path, entities, entity_type, i, field, data)
            else:
                # Special action to be dispatched
                action = DeferrableAction(
                    [entity_type, i, field],
                    [path, entities, entity_type, field, i, data],
                    extractor_action)
                action.run()
                # If the action throws an exception (usually reference to something not yet created)
                # --then we allow for it to be resolved later
                if action.complete:
                    action.resolve(entities)
                else:
                    failed_actions.append(action)
                i += 1
    return failed_actions


def validate_entity_payload_id(entity_payload):
    id_ = entity_payload.get('id', None)
    try:
        uuid.UUID(id_, version=4)
        return None
    except (ValueError, AttributeError, TypeError):
        return {'description': 'Entity id "{}" is not a valid uuid'.format(id_)}


def validate_avro(schema, datum):
    result = avro_tools.AvroValidator(
        schema=parse_schema(json.dumps(schema)),
        datum=datum,
    )
    errors = []
    for error in result.errors:
        errors.append({
            'description': avro_tools.format_validation_error(error),
        })
    return errors


def validate_entities(entities, schemas):
    validation_errors = []
    validated_entities = collections.defaultdict(list)
    for entity_name, entity_payloads in entities.items():
        for entity_payload in entity_payloads:
            entity_errors = []
            id_error = validate_entity_payload_id(entity_payload)
            if id_error:
                entity_errors.append(id_error)
            schema_definition = schemas[entity_name]
            avro_validation_errors = validate_avro(
                schema=schema_definition,
                datum=entity_payload,
            )
            entity_errors.extend(avro_validation_errors)
            if entity_errors:
                validation_errors.extend(entity_errors)
            else:
                validated_entities[entity_name].append(entity_payload)

    return EntityValidationResult(
        validation_errors=validation_errors,
        entities=validated_entities,
    )


def extract_entities(requirements, response_data, entity_definitions, schemas):
    data = response_data if response_data else []
    data['aether_errors'] = []
    # for output. Since we need to submit the extracted entities as different
    # types, it's helpful to seperate them here
    entities = {}
    # entity names that have requirements
    required_entities = requirements.keys()
    # sometimes order matters and our custom actions failed. We'll put them here
    failed_actions = []
    for entity_type in required_entities:
        entity_stub = get_entity_stub(
            requirements, entity_definitions, entity_type, data)
        # extract the entity pushing failures onto failed actions
        failed_actions.extend(
            extract_entity(
                entity_type, entities, requirements, data, entity_stub)
        )

    failed_again = []
    for action in failed_actions:
        # these actions failed, so we'll try again,
        # hoping it was caused by ordering of mapping instructions (it usually is...)
        action.run()
        if not (action.complete):
            failed_again.append(action)
        else:
            action.resolve(entities)
    # send a log of paths with errors to the user via saved response
    for action in failed_again:
        error = 'Failure: "{}"'.format(action.error)
        data['aether_errors'].append(error)
    validation_result = validate_entities(entities, schemas)
    data['aether_errors'].extend(validation_result.validation_errors)
    return data, validation_result.entities


def extract_create_entities(submission_payload, mapping_definition, schemas):

    # Get entity definitions
    entity_defs = get_entity_definitions(mapping_definition, schemas)

    # Get field mappings
    field_mappings = get_field_mappings(mapping_definition)

    # Get entity requirements
    requirements = get_entity_requirements(entity_defs, field_mappings)

    # Only attempt entity extraction if requirements are present
    submission_data = {'aether_errors': []}
    entity_types = {}
    if any(requirements.values()):
        submission_data, entity_types = extract_entities(
            requirements,
            submission_payload,
            entity_defs,
            schemas,
        )

    entities = []
    for projectschema_name, entity_payloads in entity_types.items():
        for entity_payload in entity_payloads:
            entity = Entity(
                payload=entity_payload,
                projectschema_name=projectschema_name,
                status='Publishable',
            )
            entities.append(entity)
    return submission_data, entities


def run_entity_extraction(submission):
    # Extract entity for each mapping in the submission.mappingset
    mappings = models.Mapping.objects.filter(mappingset=submission.mappingset)
    for mapping in mappings:
        if mapping.is_active:
            mapping_definition = mapping.definition
            # Get the primary key of the projectschema
            # entity_pks = list(mapping_definition['entities'].values())
            entity_ps_ids = mapping_definition.get('entities')
            # Save submission and exit early if mapping does not specify any entities.
            if not entity_ps_ids:
                submission.save()
                return
            # Get the schema of the projectschema
            project_schemas = {
                name: models.ProjectSchema.objects.get(pk=_id)
                for name, _id in entity_ps_ids.items()
            }
            schemas = {
                name: ps.schema.definition
                for name, ps in project_schemas.items()
            }
            submission.save()
            _, entities = extract_create_entities(
                submission_payload=submission.payload,
                mapping_definition=mapping_definition,
                schemas=schemas,
            )
            for entity in entities:
                projectschema_name = entity.projectschema_name
                projectschema = project_schemas[projectschema_name]
                entity_instance = models.Entity(
                    payload=entity.payload,
                    status=entity.status,
                    projectschema=projectschema,
                    submission=submission,
                    mapping=mapping,
                    mapping_revision=mapping.revision
                )
                entity_instance.save()


def merge_objects(source, target, direction):
    # Merge 2 objects
    #
    # Default merge operation is prefer_new
    # Params <source='Original object'>, <target='New object'>,
    # <direction='Direction of merge, determins primacy:
    # use constants.MergeOptions.[prefer_new, prefer_existing]'>
    # # direction Options:
    # prefer_new > (Target to Source) Target takes primacy,
    # prefer_existing > (Source to Target) Source takes primacy
    result = {}
    if direction and direction == constants.MergeOptions.fww.value:
        for key in source:
            target[key] = source[key]
        result = target
    else:
        for key in target:
            source[key] = target[key]
        result = source
    return result


def validate_payload(schema_definition, payload):
    # Use spavro to validate payload against the linked schema
    try:
        avro_schema = parse_schema(json.dumps(schema_definition))
        valid = validate(avro_schema, payload)
        if not valid:
            msg = 'Extracted record did not conform to registered schema'
            raise EntityValidationError(msg)
        return True
    except Exception as err:
        raise err
