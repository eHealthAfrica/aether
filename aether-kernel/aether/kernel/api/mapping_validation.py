import collections

from jsonpath_ng import parse

MESSAGE_NO_MATCH = 'No match for path'

Success = collections.namedtuple('Success', ['path', 'result'])
Failure = collections.namedtuple('Failure', ['path', 'error_message'])


def validate_getter(obj, path):
    if path.startswith('#!'):
        return Success(path, [])
    result = [
        datum.value for datum in
        parse(path).find(obj)
    ]
    if result:
        return Success(path, result)
    return Failure(path, MESSAGE_NO_MATCH)


def validate_setter(entity_list, path):
    path_segments = path.split('.')
    schema_name = path_segments[0]
    setter = '.'.join(['$'] + path_segments[1:])
    for entity in entity_list:
        if entity.projectschema_name == schema_name:
            result = [
                datum.value for datum in
                parse(setter).find(entity.payload)
            ]
            if result:
                return Success(path, result)
    return Failure(path, MESSAGE_NO_MATCH)


def validate_mapping(submission_payload, entity_list, mapping):
    getter, setter = mapping
    return (
        validate_getter(submission_payload, getter),
        validate_setter(entity_list, setter),
    )


def validate_mappings(submission_payload, entity_list, mapping_definition):
    errors = []
    for mapping in mapping_definition['mapping']:
        for result in validate_mapping(submission_payload, entity_list, mapping):
            if isinstance(result, Failure):
                errors.append(result)
    return errors
