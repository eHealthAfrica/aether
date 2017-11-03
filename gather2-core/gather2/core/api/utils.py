import string
import json
import uuid
from jsonpath_ng import parse
from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer
from pygments.lexers.python import Python3Lexer


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


def get_field_mappings(mapping_definition):
    mapping_obj = mapping_definition
    matches = parse("mapping[*]").find(mapping_obj)
    mappings = [match.value for match in matches]
    return mappings


def JSP_get_basic_fields(avro_obj):
    jsonpath_expr = parse('fields[*].name')
    return [match.value for match in jsonpath_expr.find(avro_obj)]


def get_entity_definitions(mapping_definition, schema):
    required_entities = {}
    mapping = mapping_definition
    found_entities = parse("entities[*]").find(mapping)
    entities = [match.value for match in found_entities][0]
    for entity_definition in entities.items():
        entity_name, file_name = entity_definition
        required_entities[entity_name] = JSP_get_basic_fields(schema)
    return required_entities


def get_entity_requirements(entities, field_mappings):
    all_requirements = {}
    for entity_name, entity_definition in entities.items():
        entity_requirements = {}
        # find mappings that start with the entity name
        # and return a list with the entity_name ( and dot ) removed from the destination
        matching_mappings = [[src, dst.split(entity_name+".")[1]]
                             for src, dst in field_mappings
                             if dst.startswith(entity_name+".")]
        for field in entity_definition:
            # filter again to find sources pertaining to this particular field in this entity
            field_sources = [src for src, dst in matching_mappings if dst == field]
            entity_requirements[field] = field_sources
        all_requirements[entity_name] = entity_requirements
    return all_requirements


def resolve_entity_reference(entity_jsonpath, constructed_entities, entity_name, field_name, instance_number, source_data):
    #called via  #!entity-reference#jsonpath
    #looks inside of the entities to be exported as currently constructed
    #returns the value(s) found at entity_jsonpath
    return "this is a dummy value!"


def get_or_make_uuid(entity_name, field_name, instance_number, source_data):
    #either uses a pre-created uuid present in source_data
    #--or-- creates a new uuid and saves it in source data
    # make one uuid, we may not use it
    value = str(uuid.uuid4())
    base = "aether_extractor_enrichment"
    if source_data.get(base, {}).get(entity_name, {}).get(field_name):
        try:
            value = source_data.get(base, {}).get(entity_name).get(field_name)[instance_number]
        except IndexError as e:
            source_data[base][entity_name][field_name].append(value)
        finally:
            return value
    else:
        # create as little as the heirarchy as required
        # there's a better way to do this with collections.defaultdict
        if not source_data.get(base):
            source_data[base] = {}
        if not source_data[base].get(entity_name):
            source_data[base][entity_name] = {}
        if not source_data[base][entity_name].get(field_name):
            source_data[base][entity_name][field_name] = [value]
        else:
            source_data[base][entity_name][field_name].append(value)
        return value

def resolve_action(source_path):
    #take a path instuction (like #!uuid# or #!entity-reference#a.json[path]) and resolves the action and arguments
    opts = source_path.split("#!")[1].split("#")
    #action string is between #! and #
    action = opts[0]
    #if arguments are present we'll try and parse them
    args = opts[-1] if len(opts) > 1 else None
    if args:
        try:
            #see if we can parse json from the argument
            args = json.loads(args)
        except ValueError:
            #not a json value so we'll leave it alone
            pass
    else:
        #in case args is an empty string
        args = None
    return action , args


def extractor_action(source_path, constructed_entities, entity_name, field_name, instance_number, source_data):
    #takes an extractor action instuction (#!action#args) and dispatches it to the proper funciton
    action , args = resolve_action(source_path)
    if action == "uuid":
        return get_or_make_uuid(entity_name, field_name, instance_number, source_data)
    elif action == "entity-reference":
        resolve_entity_reference(args, constructed_entities, entity_name, field_name, instance_number, source_data)        
    else:
        raise ValueError("No action by name %s" % action)        


def extract_entity(requirements, response_data, entity_stubs):
    data = None
    if response_data:
        data = response_data

    # for output. Since we need to submit the extracted entities as different
    # types, it's helpful to seperate them here
    entities = {}
    # entitie names that have requirements
    required_entities = requirements.keys()
    for entity_name in required_entities:
        # copy an empty instance of available fields
        entity_stub = {k: [] for k in entity_stubs.get(entity_name)}
        # do a quick first resolution of paths to size output requirement
        for field, paths in requirements.get(entity_name).items():
            for i, path in enumerate(paths):
                #if this is a json path, we'll resolve it to see how big the result is
                if not "#!" in path:
                    matches = parse(path).find(data)
                    [entity_stub[field].append(match.value) for match in matches]
                else:
                    entity_stub[field].append(path)
        # calculate how many instances we need to split the resolved data
        # into by maximum number of path resolutions
        count = max([len(entity_stub.get(field)) for field in entity_stub.keys()])
        # make empty stubs for our expected outputs. One for each member
        # identified in count process
        entities[entity_name] = [{} for i in range(count)]

        # iterate required fields, resolve paths and copy data to stubs
        for field, paths in requirements.get(entity_name).items():
            # ignore fields with empty paths
            if len(paths) < 1:
                continue
            # iterate over expected output entities
            for i in range(count):
                # if fewer paths than required use the last value
                # otherwise use the current path
                path = paths[-1] if len(paths) < (i + 1) else paths[i]
                # check to see if we need to use a UUID here
                if not "#!"in path:
                    # find the matches and assign them
                    matches = parse(path).find(data)
                    if len(matches) < 2:
                        # single value
                        entities[entity_name][i][field] = matches[0].value
                    else:
                        # multiple values, choose the one aligned with this entity (#i)
                        entities[entity_name][i][field] = matches[i].value
                else:
                    #Special action to be dispatched
                    #entities[entity_name][i][field] = get_or_make_uuid(entity_name, field, i, data)
                    entities[entity_name][i][field] = extractor_action(path, entities, entity_name, field, i, data)

    return data, entities
