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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from dateutil import parser

from pyxform import builder, xls2json, xform2json
from pyxform.xls2json_backends import xls_to_dict
from pyxform.xform_instance_parser import XFormInstanceParser


# ------------------------------------------------------------------------------
# Parser methods
# ------------------------------------------------------------------------------

def parse_file(filename, content):
    '''
    Depending on the file extension parses file content into an XML string.
    This method does not validate the content itself.
    '''

    if filename.endswith('.xml'):
        return parse_xmlform(content)
    else:
        return parse_xlsform(content)


def parse_xlsform(fp):
    '''
    Parses XLS file content into an XML string.
    '''

    xform_dict = xls_to_dict(fp)
    settings = xform_dict['settings'][0]
    name = settings['instance_name'] if 'instance_name' in settings else None
    language = settings['default_language'] if 'default_language' in settings else 'default'

    json_survey = xls2json.workbook_to_json(
        workbook_dict=xform_dict,
        form_name=name,
        default_language=language,
        warnings=[],
    )
    survey = builder.create_survey_element_from_dict(json_survey)
    return survey.xml().toprettyxml(indent='  ')


def parse_xmlform(fp):
    '''
    Parses XML file content into an XML string. Checking that the content is a
    valid XML.
    '''

    content = fp.read().decode('utf-8')
    # check that the file content is a valid XML
    __parse_xml_to_dict(content)
    # but return the untouched content if it does not raise any exception
    return content


def validate_xform(xml_definition):
    '''
    Validates xForm definition
    '''

    try:
        xform_dict = __parse_xml_to_dict(xml_definition)
    except Exception:
        raise TypeError('not valid xForm definition')

    if (
        'html' not in xform_dict
        or 'body' not in xform_dict['html']
        or 'head' not in xform_dict['html']
        or 'model' not in xform_dict['html']['head']
        or 'bind' not in xform_dict['html']['head']['model']
    ):
        raise TypeError('not valid xForm definition')

    instance = __get_xform_instance(xform_dict)

    head = xform_dict['html']['head']
    title = head['title'] if 'title' in head else None
    form_id = instance['id'] if 'id' in instance else None

    if not title and not form_id:
        raise TypeError('missing title and form_id')

    if not title:
        raise TypeError('missing title')

    if not form_id:
        raise TypeError('missing form_id')


def parse_submission(data, xml_definition):
    '''
    Transforms and cleans the dictionary submission.

    From:

        {
            'ZZZ': {
                '@id': 'form-id',
                '@version': 'v1,
                ...
                'choice_a': 'id_1',
                'number_b': '1',
                ...
            }
        }

    Into:

        {
            '@id': 'form-id',
            '@version': 'v1,
            ...
            'choice_a': 'value_1',
            'number_b': 1,
            ...
        }
    '''

    def walk(obj, parent_keys=[]):
        for k, v in obj.items():
            keys = parent_keys + [k]
            xpath = '/' + '/'.join(keys)
            _type = xpath_types.get(xpath)

            if _type == 'repeat' and not isinstance(v, list):
                # list of one item but not presented as a list
                # transform it back into a list
                obj[k] = [v]

            if isinstance(v, dict):
                walk(v, keys)

            elif isinstance(v, list):
                for i in v:
                    # indices are not important
                    walk(i, keys)

            elif v is not None:
                # parse specific type values
                # the rest of them remains the same (as string)

                if _type in ('int', 'integer', 'long', 'short'):
                    obj[k] = int(v)

                if _type in ('decimal', 'double', 'float'):
                    obj[k] = float(v)

                if _type in ('date', 'dateTime'):
                    obj[k] = parser.parse(v).isoformat()

                if _type == 'geopoint':
                    lat, lng, altitude, accuracy = v.split()
                    obj[k] = {
                        'coordinates': [float(lat), float(lng)],
                        'altitude': float(altitude),
                        'accuracy': float(accuracy),
                        'type': 'Point',
                    }

            else:
                if _type == 'geopoint':
                    # to prevent further errors, in case of null values
                    # return the same structure but with null values
                    obj[k] = {
                        'coordinates': [],
                        'altitude': None,
                        'accuracy': None,
                        'type': None,
                    }
                elif _type == 'repeat':
                    # null arrays are handled as empty arrays
                    obj[k] = []
            else:
                obj[k] = None

    xpath_types = __get_nodeset_types(xml_definition)
    walk(data)  # modifies inplace

    # assumption: there is only one child that represents the form content
    # usually: {'ZZZ': { ... }}
    # remove this first level and return content
    if len(list(data.keys())) == 1:  # pragma: no cover
        data = data[list(data.keys())[0]]

    return data


# ------------------------------------------------------------------------------
# Getter methods
# ------------------------------------------------------------------------------

def get_xform_data_from_xml(xml_definition):
    '''
    Extracts the meaningful data from the xForm.
    '''

    xform_dict = __parse_xml_to_dict(xml_definition)

    title = xform_dict['html']['head']['title']
    instance = __get_xform_instance(xform_dict)

    form_id = instance['id']
    version = instance['version'] if 'version' in instance else None

    return title, form_id, version


def get_instance_data_from_xml(xml_content):
    '''
    Parses the XML submission into a dictionary,
    also extracts the form id and the form version.
    '''

    xform_parser = XFormInstanceParser(xml_content.decode('utf-8'))

    instance_dict = xform_parser.to_json_dict()
    form_id = xform_parser.get_xform_id_string()
    version = xform_parser.get_attributes().get('version') or '0'

    # include attributes in instance content
    root = xform_parser.get_root_node_name()
    for k, v in xform_parser.get_attributes().items():
        instance_dict[root][f'@{k}'] = v

    instance_dict[root]['@id'] = form_id
    instance_dict[root]['@version'] = version

    return instance_dict, form_id, version


def get_instance_id(instance_dict):
    '''
    Extracts device instance id from xml data
    '''

    try:
        return instance_dict['meta']['instanceID']
    except Exception:
        return None


# ------------------------------------------------------------------------------
# Private methods
# ------------------------------------------------------------------------------

def __parse_xml_to_dict(xml_content):
    '''
    Parses XML file content into an dictionary.
    '''

    return xform2json.XFormToDict(xml_content).get_dict()


def __get_xform_instance(xform_dict):
    '''
    Extracts instance from xForm definition
    '''

    try:
        instance = xform_dict['html']['head']['model']['instance']

        # this can be a list of instances or one entry
        if isinstance(instance, list):
            instances = instance
            instance = None

            for i in instances:
                # the default instance is the only one without "id"
                if 'id' not in i:
                    instance = i
                    break

        if isinstance(instance, dict):
            # assumption: there is only one child (key)
            key = list(instance.keys())[0]
            return instance[key]

        else:
            raise TypeError('missing instance definition')

    except Exception:
        raise TypeError('missing instance definition')


def __get_nodeset_types(xml_definition):
    '''
    Extract nodeset types from the xForm definition (in XML format).
    '''

    nodeset_types = {}
    xform_dict = __parse_xml_to_dict(xml_definition)

    for entries in __find_in_dict('bind', xform_dict):
        if isinstance(entries, dict):
            entries = [entries]
        for bind_entry in entries:
            if 'type' in bind_entry:
                nodeset = bind_entry['nodeset']
                nodeset_type = bind_entry['type']
                nodeset_types[nodeset] = nodeset_type

    # search in body all the repeat entries
    for entries in __find_in_dict('repeat', xform_dict):
        if isinstance(entries, dict):
            entries = [entries]
        for repeat_entry in entries:
            nodeset = repeat_entry['nodeset']
            nodeset_types[nodeset] = 'repeat'

    return nodeset_types


def __find_in_dict(key, dictionary):
    # https://gist.github.com/douglasmiranda/5127251
    # it could return a list, a dict, or a primitive value
    for k, v in dictionary.items():
        if k == key:
            yield v

        elif isinstance(v, dict):
            for result in __find_in_dict(key, v):
                yield result

        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    for result in __find_in_dict(key, d):
                        yield result
