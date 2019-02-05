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
import fnmatch
import json
import logging
import re
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext as _

from jsonpath_ng.ext import parse as jsonpath_ng_ext_parse

from ..settings import LOGGING_LEVEL

from . import models
from .validators import validate_entities
from .utils import object_contains


logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)


Entity = collections.namedtuple(
    'Entity',
    ['payload', 'projectschema_name', 'status'],
)

ENTITY_EXTRACTION_ERRORS = 'aether_errors'
ENTITY_EXTRACTION_ENRICHMENT = 'aether_extractor_enrichment'

# RegEx for jsonpaths containing a partial wildcard as a key:
# $.path.to[*].key_* where the matching path might be $.path.to[1].key_1
# or with invertes position:
# $.path.key_*.to[*].field for $.path.key_27.to[1].field
CUSTOM_JSONPATH_WILDCARD_REGEX = re.compile(
    r'(\$)?(\.)?([a-zA-Z0-9_-]*(\[.*\])*\.)?[a-zA-Z0-9_-]+\*')

# RegEx for the part of a JSONPath matching the previous RegEx which is non-compliant with the
# JSONPath spec.
# Ex: key_* in the path $.path.key_*.to[*].field
INCOMPLETE_JSON_PATH_REGEX = re.compile(r'[a-zA-Z0-9_-]+\*')

CONSTANT_TYPE_COERCIONS = {
    'int': lambda x: int(x),
    'boolean': lambda x: bool(x),
    'string': lambda x: str(x),
    'float': lambda x: float(x),
    'json': lambda x: json.loads(x)
}


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
            try:
                CachedParser.cache[path] = jsonpath_ng_ext_parse(path)
            except Exception as err:  # jsonpath-ng raises the base exception type
                new_err = _('exception parsing path {path} : {error} ').format(
                    path=path, error=err
                )
                logger.error(new_err)
                raise ValidationError(new_err) from err

        return CachedParser.cache[path]

    @staticmethod
    def find(path, obj):
        # find is an optimized call with a potentially cached parse object.
        parser = CachedParser.parse(path)
        return parser.find(obj)


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
    match = CUSTOM_JSONPATH_WILDCARD_REGEX.match(path)
    if match:
        # If `path` matches our criteria for a custom jsonpath, split `path` in
        # two parts based on the span of the regex.
        #
        # Example: given a `path` like `dose-*.id`, this will result in:
        #
        #     prefix = 'dose-'
        #     standard_jsonpath = '*.id'

        # first part of path before wildcard
        prefix = path[:match.end()].replace('$.', '')
        # replace any indexed portion with a wildcard for use in fnmatch filtering
        # because a valid jsonpath like item[0] is reported as item.[0] when matched
        # by jsonpath-ng
        wild_path = re.sub(r'(\[.*\])+', '*', prefix)
        illegal = INCOMPLETE_JSON_PATH_REGEX.search(path)
        standard_jsonpath = path[:illegal.start()] + '*' + path[illegal.end():]

        # Perform an standard jsonpath search.
        matches = CachedParser.find(standard_jsonpath, obj)
        # filter matching jsonpathes for adherence to partial wildpath
        matching_paths = fnmatch.filter(
            [str(i.full_path) for i in matches], wild_path)
        return [i for i in matches if str(i.full_path) in matching_paths]

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
        start_string = entity_type+'.'
        matching_mappings = [[src, dst.split(start_string)[1]]
                             for src, dst in field_mappings
                             if dst.startswith(start_string)]
        for field in entity_definition:
            # filter again to find sources pertaining to this particular field in this entity
            # can match an sub-element in this field.
            # "name.last" would pertain to the "name" field.
            field_sources = {}  # allows us to add nested fields and then add them to reqs
            for src, dst in matching_mappings:
                if dst == field or (dst.split('.')[0] == field):
                    curr = field_sources.get(dst, [])
                    curr.append(src)
                    field_sources[dst] = curr

            for _field, src in field_sources.items():
                entity_requirements[_field] = src
        all_requirements[entity_type] = entity_requirements
    return all_requirements


def get_entity_stub(requirements, entity_definitions, entity_name, source_data):
    # takes an entity definition and returns an empty "stub" instance to be populated
    # copy an empty instance of available fields
    entity_stub = {k: [] for k in entity_definitions.get(entity_name)}
    # do a quick first resolution of paths to size output requirement
    for field, paths in requirements.get(entity_name).items():
        if field not in entity_stub.keys() and len(paths) > 0:
            entity_stub[field] = []  # add missing deep paths
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
        nest_object(entities[p[0]][p[1]], p[2], self.res)  # handle deep paths
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


def coerce(v, _type='string'):
    # Takes a value and tries to cast it to _type.
    # Optionally can parse JSON.
    try:
        fn = CONSTANT_TYPE_COERCIONS[_type]
    except KeyError:
        raise ValueError(_('{type} not in available types for constants, {constants}').format(
            type=_type,
            constants=[i for i in CONSTANT_TYPE_COERCIONS.keys()],
        ))
    try:
        return fn(v)
    except ValueError:
        raise ValueError(_('value: {value} could not be coerced to type {type}').format(
            value=v,
            type=_type,
        ))


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


def anchor_reference(source, context, source_data, instance_number):
    # Anchors entity-referenced object to a context. See resolve_entity_reference
    try:
        this_obj = None
        obj_matches = find_by_jsonpath(source_data, source)
        if len(obj_matches) >= instance_number:
            this_obj = obj_matches[instance_number].value
        else:
            raise ValueError(_('source: {} unresolved').format(str(source)))
        obj_matches = find_by_jsonpath(source_data, context)
        if not obj_matches:
            raise ValueError(_('context: {} unresolved').format(str(context)))
        for idx, match in enumerate(obj_matches):
            if object_contains(this_obj, match.value):
                return idx
        raise ValueError(_('Object match not found in context'))
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
        raise ValueError(
            _('path {} has no matches; aborting').format(entity_jsonpath))
    if len(matches) < 2:
        # single value
        return matches[0].value
    else:
        # multiple values, attempt to choose the one aligned with this entity (#i)
        return matches[instance_number].value


def nest_object(obj, path, value):
    # this allows us to treat 'fields' as paths with depths >1
    # so that we can create structures as we fill them
    keys = path.split('.')
    # simple behavior
    if len(keys) < 2:
        obj[path] = value
        return
    else:
        if not obj.get(path, None):  # remove empty reference of base object
            try:
                del obj[path]
            except KeyError:
                pass
        obj = put_nested(obj, keys, value)
        return


def put_nested(_dict, keys, value):
    # recursively puts a value deep into a dictionary at path [k1.k2.kn]
    if len(keys) > 1:
        try:
            _dict[keys[0]] = put_nested(_dict[keys[0]], keys[1:], value)
        except KeyError:  # Level doesn't exist yet
            _dict[keys[0]] = put_nested({}, keys[1:], value)
    else:
        _dict[keys[0]] = value
    return _dict


def resolve_source_reference(path, entities, entity_name, i, field, data):
    # called via normal jsonpath as source
    # is NOT defferable as all source data should be present at extractor start
    # assignes values directly to entities within function and return new offset value (i)
    matches = find_by_jsonpath(data, path)
    if not matches:
        nest_object(entities[entity_name][i], field, None)
        i += 1
    elif len(matches) == 1:
        # single value
        nest_object(entities[entity_name][i], field, matches[0].value)
        i += 1
    else:
        for x, match in enumerate(matches):
            # multiple values, choose the one aligned with this entity (#i) & order of match(x)
            nest_object(entities[entity_name][i], field, matches[x].value)
            i += 1
    return i


def get_or_make_uuid(entity_type, field_name, instance_number, source_data):
    # Either uses a pre-created uuid present in source_data --or-- creates a new
    # uuid and saves it in source data make one uuid, we may not use it
    value = str(uuid.uuid4())
    base = ENTITY_EXTRACTION_ENRICHMENT
    if source_data.get(base, {}).get(entity_type, {}).get(field_name):
        try:
            value = source_data.get(base, {}).get(
                entity_type).get(field_name)[instance_number]
        except IndexError:
            source_data[base][entity_type][field_name].append(value)
        finally:
            return value
    else:
        # create as little as the hierarchy as required
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
        raise ValueError(_('No action with name {}').format(action))


def extract_entity(entity_type, entities, requirements, data, entity_stub):
    failed_actions = []
    # calculate how many instances we need to split the resolved data
    # into by maximum number of path resolutions
    count = max([len(entity_stub.get(field)) for field in entity_stub.keys()])
    # make empty stubs for our expected outputs. One for each member
    # identified in count process
    entities[entity_type] = [
        {field: None for field in entity_stub.keys()
            if field in requirements.get(entity_type)}  # make sure there are mappings
        for i in range(count)]

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


def extract_entities(requirements, response_data, entity_definitions, schemas):
    data = response_data if response_data else []
    data[ENTITY_EXTRACTION_ERRORS] = []
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
        data[ENTITY_EXTRACTION_ERRORS].append(error)
    validation_result = validate_entities(entities, schemas)
    data[ENTITY_EXTRACTION_ERRORS].extend(validation_result.validation_errors)
    return data, validation_result.entities


def extract_create_entities(submission_payload, mapping_definition, schemas):

    # Get entity definitions
    entity_defs = get_entity_definitions(mapping_definition, schemas)

    # Get field mappings
    field_mappings = get_field_mappings(mapping_definition)

    # Get entity requirements
    requirements = get_entity_requirements(entity_defs, field_mappings)

    # Only attempt entity extraction if requirements are present
    submission_data = {ENTITY_EXTRACTION_ERRORS: []}
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


@transaction.atomic
def run_entity_extraction(submission, overwrite=False):
    if overwrite:
        # FIXME:
        # there should be a better way to detect the generated entities and
        # replace their payloads with the new ones
        submission.entities.all().delete()

    # Extract entity for each mapping in the submission.mappingset
    mappings = submission.mappingset \
                         .mappings \
                         .filter(is_active=True) \
                         .exclude(definition={}) \
                         .exclude(definition__entities__isnull=True) \
                         .exclude(definition__entities={})

    for mapping in mappings:
        # Get the primary key of the projectschema
        entity_ps_ids = mapping.definition.get('entities')
        # Get the schema of the projectschema
        project_schemas = {
            name: models.ProjectSchema.objects.get(pk=_id)
            for name, _id in entity_ps_ids.items()
        }
        schemas = {
            name: ps.schema.definition
            for name, ps in project_schemas.items()
        }
        _, entities = extract_create_entities(
            submission_payload=submission.payload,
            mapping_definition=mapping.definition,
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

    # this should include in the submission payload the following properties
    # generated during the extraction:
    # - ``aether_errors``, with all the errors that made not possible
    #   to create the entities.
    # - ``aether_extractor_enrichment``, with the generated values that allow us
    #   to re-execute this process again with the same result.
    submission.save()
