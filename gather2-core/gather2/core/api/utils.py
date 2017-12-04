import string
import json
import re
import uuid

import jsonpath_ng
from jsonpath_ng import parse

from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer
from pygments.lexers.python import Python3Lexer

from . import models


class EntityExtractionError(Exception):
    pass


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


custom_jsonpath_wildcard_regex = re.compile('(\$\.)?[a-zA-Z0-9_-]+\*')


def find_by_jsonpath(obj, path):
    """
    This function wraps `jsonpath_ng.parse()` and
    `jsonpath_ng.jsonpath.Child.find()` in order to provide custom
    functionality as described in https://jira.ehealthafrica.org/browse/AET-38.

    If the first element in `path` is a wildcard match prefixed by an arbitrary
    string, `find` will attempt to filter the results by that prefix.

    **NOTE**: this behavior is not part of jsonpath spec.
    """

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
        standard_jsonpath = path[split_pos:]
        # Perform an standard jsonpath search.
        result = []
        for datum in jsonpath_ng.parse(standard_jsonpath).find(obj):
            full_path = str(datum.full_path)
            # Only include datum if its full path starts with `prefix`.
            if full_path.startswith(prefix):
                result.append(datum)
        return result
    else:
        # Otherwise, perform a standard jsonpath search of `obj`.
        return jsonpath_ng.parse(path).find(obj)


def get_field_mappings(mapping_definition):
    mapping_obj = mapping_definition
    matches = parse("mapping[*]").find(mapping_obj)
    mappings = [match.value for match in matches]
    return mappings


def JSP_get_basic_fields(avro_obj):
    jsonpath_expr = parse('fields[*].name')
    return [match.value for match in jsonpath_expr.find(avro_obj)]


def get_entity_definitions(mapping_definition, schemas):
    required_entities = {}
    found_entities = parse("entities[*]").find(mapping_definition)
    entities = [match.value for match in found_entities][0]
    for entity_definition in entities.items():
        entity_type, file_name = entity_definition
        required_entities[entity_type] = JSP_get_basic_fields(schemas.get(entity_type))
    return required_entities


def get_entity_requirements(entities, field_mappings):
    all_requirements = {}
    for entity_type, entity_definition in entities.items():
        entity_requirements = {}
        # find mappings that start with the entity name
        # and return a list with the entity_type ( and dot ) removed from the destination
        matching_mappings = [[src, dst.split(entity_type+".")[1]]
                             for src, dst in field_mappings
                             if dst.startswith(entity_type+".")]
        for field in entity_definition:
            # filter again to find sources pertaining to this particular field in this entity
            field_sources = [src for src, dst in matching_mappings if dst == field]
            entity_requirements[field] = field_sources
        all_requirements[entity_type] = entity_requirements
    return all_requirements


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
    # Called via #!none acts as a dummy instruction when you need to the first
    # entity to have a value but no others
    return None


def action_constant(args):
    # Called via #!constant#args returns the arguments to be assigned as the
    # value for the path
    return args


def resolve_entity_reference(
        entity_jsonpath,
        constructed_entities,
        entity_type,
        field_name,
        instance_number,
        source_data,
):
    # Called via #!entity-reference#jsonpath looks inside of the entities to be
    # exported as currently constructed returns the value(s) found at
    # entity_jsonpath
    matches = parse(entity_jsonpath).find(constructed_entities)
    if len(matches) < 1:
        raise ValueError("path %s has no matches; aborting" % entity_jsonpath)
    if len(matches) < 2:
        # single value
        return matches[0].value
    else:
        # multiple values, choose the one aligned with this entity (#i)
        return matches[instance_number].value


def get_or_make_uuid(entity_type, field_name, instance_number, source_data):
    # Either uses a pre-created uuid present in source_data --or-- creates a new
    # uuid and saves it in source data make one uuid, we may not use it
    value = str(uuid.uuid4())
    base = "aether_extractor_enrichment"
    if source_data.get(base, {}).get(entity_type, {}).get(field_name):
        try:
            value = source_data.get(base, {}).get(entity_type).get(field_name)[instance_number]
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
    opts = source_path.split("#!")[1].split("#")
    # Action string is between #! and #
    action = opts[0]
    # If arguments are present we'll try and parse them
    args = opts[-1] if len(opts) > 1 else None
    if args:
        try:
            # See if we can parse json from the argument
            args = json.loads(args)
        except ValueError:
            # Not a json value so we'll leave it alone
            pass
    else:
        # In case args is an empty string
        args = None
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
    if action == "uuid":
        return get_or_make_uuid(entity_type, field_name, instance_number, source_data)
    elif action == "entity-reference":
        return resolve_entity_reference(
            args,
            constructed_entities,
            entity_type,
            field_name,
            instance_number,
            source_data,
        )
    elif action == "none":
        return action_none()
    elif action == "constant":
        return action_constant(args)
    else:
        raise ValueError("No action with name %s" % action)


def extract_entity(requirements, response_data, entity_stubs):
    data = {}
    if response_data:
        data = response_data
    data["aether_errors"] = []
    # Sometimes order matters and our custom actions failed. We'll put them here
    failed_actions = []
    # For output. Since we need to submit the extracted entities as different
    # types, it's helpful to seperate them here
    entities = {}
    # entity names that have requirements
    required_entities = requirements.keys()
    for entity_type in required_entities:
        # Copy an empty instance of available fields
        entity_stub = {k: [] for k in entity_stubs.get(entity_type)}
        # Do a quick first resolution of paths to size output requirement
        for field, paths in requirements.get(entity_type).items():
            for i, path in enumerate(paths):
                # If this is a json path, we'll resolve it to see how big the result is
                if "#!" not in path:
                    matches = parse(path).find(data)
                    [entity_stub[field].append(match.value) for match in matches]
                else:
                    entity_stub[field].append(path)
        # Calculate how many instances we need to split the resolved data
        # into by maximum number of path resolutions
        count = max([len(entity_stub.get(field)) for field in entity_stub.keys()])
        # Make empty stubs for our expected outputs. One for each member
        # identified in count process
        entities[entity_type] = [
            {field: None for field in entity_stub.keys()} for i in range(count)
        ]

        # Iterate required fields, resolve paths and copy data to stubs
        for field, paths in requirements.get(entity_type).items():
            # Ignore fields with empty paths
            if len(paths) < 1:
                for i in range(count):
                    del entities[entity_type][i][field]
                continue
            # Iterate over expected output entities.
            # Some paths will satisfy more than one entity, so we increment in
            # different places
            i = 0
            while i < count:
                # If fewer paths than required use the last value
                # otherwise use the current path
                path = paths[-1] if len(paths) < (i + 1) else paths[i]
                # Check to see if we need to use a UUID here
                if "#!" not in path:
                    # Find the matches and assign them
                    matches = parse(path).find(data)
                    if len(matches) == 0:
                        msg = 'No matches found for path: "{}"'
                        raise EntityExtractionError(msg.format(path))
                    elif len(matches) == 1:
                        # single value
                        entities[entity_type][i][field] = matches[0].value
                        i += 1
                        continue
                    else:
                        for x, match in enumerate(matches):
                            # Multiple values, choose the one aligned with this
                            # entity (#i) & order of match(x)
                            entities[entity_type][i][field] = matches[x].value
                            i += 1
                        continue
                else:
                    # Special action to be dispatched
                    action = DeferrableAction(
                        [entity_type, i, field],
                        [path, entities, entity_type, field, i, data],
                        extractor_action,
                    )
                    action.run()
                    # If the action throws an exception (usually reference to
                    # something not yet created) --then we allow for it to be
                    # resolved later
                    if action.complete:
                        action.resolve(entities)
                    else:
                        failed_actions.append(action)
                    i += 1

    failed_again = []
    for action in failed_actions:
        # These actions failed, so we'll try again, hoping it was caused by
        # ordering of mapping instructions (it usually is...)
        action.run()
        if not (action.complete):
            failed_again.append(action)
        else:
            action.resolve(entities)

    # Send a log of paths with errors to the user via saved response
    for action in failed_again:
        data["aether_errors"].append("failed %s" % action.path)

    return data, entities


def extract_create_entities(response):
    # Get the mapping definition from the response (response.mapping.definition):
    mapping_definition = response.mapping.definition

    # Get the primary key of the projectschema
    # entity_pks = list(mapping_definition['entities'].values())
    entity_ps_ids = mapping_definition.get("entities")

    # Get the schema of the projectschema
    # project_schema = models.ProjectSchema.objects.get(pk=entity_pks[0])
    project_schemas = {
        name: models.ProjectSchema.objects.get(pk=_id) for name, _id in entity_ps_ids.items()
    }
    schemas = {name: ps.schema.definition for name, ps in project_schemas.items()}
    # schema = project_schema.schema.definition

    # Get entity definitions
    entity_defs = get_entity_definitions(mapping_definition, schemas)

    # Get field mappings
    field_mappings = get_field_mappings(mapping_definition)

    # Get entity requirements
    requirements = get_entity_requirements(entity_defs, field_mappings)

    response_data = response.payload

    # Only attempt entity extraction if requirements are present
    if any(requirements.values()):
        data, entity_types = extract_entity(
            requirements,
            response_data,
            entity_defs,
        )
    else:
        entity_types = {}

    entity_list = []
    for name, entities in entity_types.items():
        for entity in entities:
            obj = {
                'id': entity['id'],
                'payload': entity,
                'status': 'Publishable',
                'projectschema': project_schemas.get(name)
            }
            entity_list.append(obj)
    # Save the response to the db
    response.save()

    # If extraction was successful, create new entities
    if entity_list:
        for e in entity_list:
            entity = models.Entity(
                id=e['id'],
                payload=e['payload'],
                status=e['status'],
                projectschema=e['projectschema'],
                response=response
            )
            entity.save()
