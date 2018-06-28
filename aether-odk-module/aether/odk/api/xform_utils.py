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
import re

from collections import defaultdict
from dateutil import parser
from xml.etree import ElementTree

from pyxform import builder, xls2json
from pyxform.xls2json_backends import xls_to_dict
from pyxform.xform_instance_parser import XFormInstanceParser
from spavro.schema import parse as parse_avro_schema, SchemaParseException

from django.utils.translation import ugettext as _


DEFAULT_XFORM_VERSION = '0'

_RE_AVRO_NAME = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)$')

MSG_ERROR_REASON = _(
    ' Reason: {error}.'
)
MSG_VALIDATION_XFORM_PARSE_ERR = _(
    'Not valid xForm definition.'
)
MSG_VALIDATION_XFORM_MISSING_TAGS_ERR = _(
    'Missing required tags: {tags}.'
)
MSG_VALIDATION_XFORM_MISSING_TITLE_INSTANCE_ID_ERR = _(
    'Missing required form title and instance ID.'
)
MSG_VALIDATION_XFORM_MISSING_TITLE_ERR = _(
    'Missing required form title.'
)
MSG_VALIDATION_XFORM_MISSING_INSTANCE_ID_ERR = _(
    'Missing required instance ID.'
)
MSG_XFORM_MISSING_INSTANCE_ERR = _(
    'Missing required instance definition.'
)


# ------------------------------------------------------------------------------
# Parser methods
# ------------------------------------------------------------------------------

def parse_xform_file(filename, content):
    '''
    Depending on the file extension parses file content into an XML string.
    This method does not validate the content itself.
    '''

    if filename.endswith('.xml'):
        return __parse_xmlform(content)
    else:
        return __parse_xlsform(content)


def parse_submission(data, xml_definition):
    '''
    Transforms and cleans the dictionary submission.

    From:

        {
            'ZZZ': {
                '_id': 'form-id',
                '_version': 'v1,
                ...
                'choice_a': 'id_1',
                'number_b': '1',
                ...
            }
        }

    Into:

        {
            '_id': 'form-id',
            '_version': 'v1,
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
                    latitude, longitude, altitude, accuracy = v.split()
                    obj[k] = {
                        'latitude': float(latitude),
                        'longitude': float(longitude),
                        'altitude': float(altitude),
                        'accuracy': float(accuracy),
                    }

            else:
                if _type == 'repeat':
                    # null arrays are handled as empty arrays
                    obj[k] = []
                else:
                    obj[k] = None

    xpath_types = {
        xpath: definition.get('type')
        for xpath, definition in __get_xform_instance_skeleton(xml_definition).items()
        if definition.get('type')
    }
    walk(data)  # modifies inplace

    # assumption: there is only one child that represents the form content
    # usually: {'ZZZ': { ... }}
    # remove this first level and return content
    keys = list(data.keys())
    if len(keys) == 1 and isinstance(data[keys[0]], dict):  # pragma: no cover
        data = data[keys[0]]

    return data


def parse_xform_to_avro_schema(xml_definition, default_version=DEFAULT_XFORM_VERSION):
    '''
    Transforms the xForm definition (in XML format) to AVRO schema.

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <itext>
                <translation default="true()" lang="AAA">
                  <text id="/a/field_1:label">
                    <value>T E X T - #1</value>
                  </text>

                  <text id="/a/field_n:label">
                    <value>T E X T - #N</value>
                  </text>
                </translation>
                <translation lang="BBB">
                  <text id="/a/field_1:label">
                    <value>U F Y U - #1</value>
                  </text>

                  <text id="/a/field_n:label">
                    <value>U F Y U - #N</value>
                  </text>
                </translation>
              </itext>

              <instance>
                <Something id="F O R M I D" version="V E R S I O N"></Something>
              </instance>
              <instance id="choice-1"></instance>
              <instance id="choice-2"></instance>

              <instance id="choice-n"></instance>

              <bind nodeset="/a/field_1" ... type="T Y P E"/>
              <bind nodeset="/a/field_2" ... type="T Y P E"/>
              <bind nodeset="/a/field_2/child_1" ... type="T Y P E"/>

              <bind nodeset="/a/field_n" ... type="T Y P E"/>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>
    '''

    title, form_id, version = get_xform_data_from_xml(xml_definition)
    version = version or default_version
    # include version within name to identify different entity source
    name = f'{form_id}_{version}'
    # AVRO names contain only [A-Za-z0-9_]
    name = ''.join([c if c.isalnum() or c == '_' else ' ' for c in name]).title().replace(' ', '')

    KEY = '-----'

    # initial schema, with "id" and "version" attributes
    avro_schema = {
        'name': name,
        'namespace': 'aether.odk.xforms',
        'doc': f'{title} (id: {form_id}, version: {version})',
        'type': 'record',
        'fields': [
            {
                'name': '_id',
                'doc': _('xForm ID'),
                'type': 'string',
                'default': form_id,
            },
            {
                'name': '_version',
                'doc': _('xForm version'),
                'type': 'string',
                'default': version,
            },
        ],
        # this is going to be removed later,
        # but it's used to speed up the build process
        KEY: None,
        # this is going to include the schema errors
        '_errors': []
    }

    xform_schema = __get_xform_instance_skeleton(xml_definition)
    for xpath, definition in xform_schema.items():
        if len(xpath.split('/')) == 2:
            # include the KEY value
            avro_schema[KEY] = xpath
            # ignore the root (already created)
            continue

        current_type = definition.get('type')
        current_name = xpath.split('/')[-1]
        current_doc = definition.get('label')

        # validate name
        try:
            __validate_avro_name(current_name)
        except SchemaParseException as e:
            avro_schema['_errors'].append(str(e))

        parent_path = '/'.join(xpath.split('/')[:-1])
        parent = list(__find_by_key_value(avro_schema, KEY, parent_path))[0]

        # nested record
        if current_type == 'group':
            parent['fields'].append({
                'name': current_name,
                'doc': current_doc,
                'type': [
                    'null',
                    {
                        'name': current_name,
                        'type': 'record',
                        'fields': [],
                        KEY: xpath,
                    },
                ],
            })

        # array
        elif current_type == 'repeat':
            parent['fields'].append({
                'name': current_name,
                'doc': current_doc,
                'type': [
                    'null',
                    {
                        'type': 'array',
                        'items': {
                            'name': current_name,
                            'type': 'record',
                            'fields': [],
                            KEY: xpath,
                        },
                    },
                ],
            })

        # there are three types of GEO types: geopoint, geotrace and geoshape
        # currently, only geopoint is implemented by ODK Collect
        elif current_type == 'geopoint':
            parent['fields'].append({
                'name': current_name,
                'doc': current_doc,
                'type': [
                    'null',
                    {
                        'name': current_name,
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'latitude',
                                'doc': _('latitude'),
                                'type': __get_avro_primitive_type('float', True),
                            },
                            {
                                'name': 'longitude',
                                'doc': _('longitude'),
                                'type': __get_avro_primitive_type('float', True),
                            },
                            {
                                'name': 'altitude',
                                'doc': _('altitude'),
                                'type': __get_avro_primitive_type('float', False),
                            },
                            {
                                'name': 'accuracy',
                                'doc': _('accuracy'),
                                'type': __get_avro_primitive_type('float', False),
                            },
                        ],
                    },
                ],
            })

        # final and simple leaf
        else:
            parent['fields'].append({
                'name': current_name,
                'type': __get_avro_primitive_type(current_type, definition.get('required')),
                'doc': current_doc,
            })

    # remove fake KEY
    __delete_key_in_dict(avro_schema, KEY)

    # validate generated schema
    __validate_avro_schema(avro_schema)
    if not avro_schema['_errors']:
        del avro_schema['_errors']

    return avro_schema


# ------------------------------------------------------------------------------
# Validator methods
# ------------------------------------------------------------------------------


class XFormParseError(Exception):
    pass


def validate_xform(xml_definition):
    '''
    Validates xForm definition.

    This XML must conform the JavaRosa specification.
    http://opendatakit.github.io/xforms-spec/
    '''

    try:
        xform_dict = __parse_xml_to_dict(xml_definition)
    except Exception as e:
        raise XFormParseError(
            MSG_VALIDATION_XFORM_PARSE_ERR +
            MSG_ERROR_REASON.format(error=str(e)))

    missing_tags = []
    if (
        'h:html' not in xform_dict
        or xform_dict['h:html'] is None
    ):
        missing_tags.append('<h:html>')
    else:
        if 'h:body' not in xform_dict['h:html']:
            missing_tags.append('<h:body> in <h:html>')

        if (
            'h:head' not in xform_dict['h:html']
            or xform_dict['h:html']['h:head'] is None
        ):
            missing_tags.append('<h:head> in <h:html>')
        else:
            if 'h:title' not in xform_dict['h:html']['h:head']:
                missing_tags.append('<h:title> in <h:html><h:head>')
            if (
                'model' not in xform_dict['h:html']['h:head']
                or xform_dict['h:html']['h:head']['model'] is None
            ):
                missing_tags.append('<model> in <h:html><h:head>')
            else:
                if (
                    'instance' not in xform_dict['h:html']['h:head']['model']
                    or xform_dict['h:html']['h:head']['model']['instance'] is None
                ):
                    missing_tags.append('<instance> in <h:html><h:head><model>')
    if missing_tags:
        raise XFormParseError(
            MSG_VALIDATION_XFORM_MISSING_TAGS_ERR.format(tags=', '.join(missing_tags))
        )

    title = xform_dict['h:html']['h:head']['h:title']
    instance = __get_xform_instance(xform_dict)
    form_id = instance.get('@id') if instance else None

    if not title and not form_id:
        raise XFormParseError(MSG_VALIDATION_XFORM_MISSING_TITLE_INSTANCE_ID_ERR)

    if not title:
        raise XFormParseError(MSG_VALIDATION_XFORM_MISSING_TITLE_ERR)

    if not form_id:
        raise XFormParseError(MSG_VALIDATION_XFORM_MISSING_INSTANCE_ID_ERR)


# ------------------------------------------------------------------------------
# Getter methods
# ------------------------------------------------------------------------------

def get_xform_data_from_xml(xml_definition):
    '''
    Extracts the meaningful data from the xForm.
    '''

    xform_dict = __parse_xml_to_dict(xml_definition)

    title = xform_dict['h:html']['h:head']['h:title']
    instance = __get_xform_instance(xform_dict)

    form_id = instance.get('@id')
    version = instance.get('@version')

    return title, form_id, version


def get_instance_data_from_xml(xml_content):
    '''
    Parses the XML submission into a dictionary,
    also extracts the form id and the form version.
    '''

    xform_parser = XFormInstanceParser(xml_content.decode('utf-8'))

    instance_dict = xform_parser.to_json_dict()
    form_id = xform_parser.get_xform_id_string()
    version = xform_parser.get_attributes().get('version') or DEFAULT_XFORM_VERSION

    root = xform_parser.get_root_node_name()

    # The instance attributes are not taking into consideration.
    # # Include attributes in instance content
    # for k, v in xform_parser.get_attributes().items():
    #     instance_dict[root][f'_{k}'] = v

    # The only ones allowed are `id` and `version` and included manually.
    instance_dict[root]['_id'] = form_id
    instance_dict[root]['_version'] = version

    try:
        instance_id = instance_dict[root]['meta']['instanceID']
    except Exception:
        instance_id = None

    return instance_dict, form_id, version, instance_id


# ------------------------------------------------------------------------------
# Private methods
# ------------------------------------------------------------------------------

def __parse_xlsform(fp):
    '''
    Parses XLS file content into an XML string.
    '''

    xform_dict = xls_to_dict(fp)
    settings = xform_dict.get('settings', [{}])[0]
    name = settings.get('instance_name')
    language = settings.get('default_language', 'default')

    json_survey = xls2json.workbook_to_json(
        workbook_dict=xform_dict,
        form_name=name,
        default_language=language,
        warnings=[],
    )
    survey = builder.create_survey_element_from_dict(json_survey)
    return survey.xml().toprettyxml(indent='  ')


def __parse_xmlform(fp):
    '''
    Parses XML file content into an XML string. Checking that the content is a
    valid XML.
    '''

    content = fp.read().decode('utf-8')
    # check that the file content is a valid XML
    __parse_xml_to_dict(content)
    # but return the untouched content if it does not raise any exception
    return content


def __parse_xml_to_dict(xml_content):
    '''
    Parses XML file content into an dictionary.
    '''

    root = ElementTree.fromstring(xml_content)
    xml_dict = __etree_to_dict(root)
    return xml_dict


def __get_xform_instance(xform_dict, with_root=False):
    '''
    Extracts instance from xForm definition
    '''

    try:
        instances = __wrap_as_list(xform_dict['h:html']['h:head']['model']['instance'])
    except Exception as e:
        raise XFormParseError(
            MSG_XFORM_MISSING_INSTANCE_ERR +
            MSG_ERROR_REASON.format(error=str(e))
        )

    instance = None
    for i in instances:
        # the default instance is the only one without "id" attribute
        if '@id' not in i:
            instance = i
            break

    if not instance or not isinstance(instance, dict):
        raise XFormParseError(MSG_XFORM_MISSING_INSTANCE_ERR)

    if with_root:
        return instance

    # assumption: there is only one child (key)
    key = list(instance.keys())[0]
    return instance[key]


def __get_xform_instance_skeleton(xml_definition):
    '''
    Extracts the xForm instance skeleton from the xForm definition (in XML format).

    The instance attributes are not taking into consideration. The only ones allowed
    are `id` and `version` and included manually in the AVRO schema.

    Will return a list with the following structure:

        - `xpath`, the field xpath within the instance.

        - `type`, the xForm data type. For an intermediate field the possible values
          are, `repeat` or `group`. Default value is string.

        - `required`, if the field is required or not. It's not relevant for
          intermediate fields.

        - `label`, the linked label of the field, in case of multilanguage takes
          the translation for the default one.
    '''

    schema = {}

    xform_dict = __parse_xml_to_dict(xml_definition)
    itexts = __get_xform_itexts(xform_dict)

    # get the default instance
    # this contains the data skeleton
    # take all the xpaths and rest of meaningful data from here
    instance = __get_xform_instance(xform_dict, with_root=True)
    for xpath, has_children in __get_all_paths(instance):
        schema[xpath] = {
            'xpath': xpath,
            'type': 'group' if has_children else 'string',
            'required': False,
            'label': __get_xform_label(xform_dict, xpath, itexts),
        }

    for entries in __find_in_dict(xform_dict, 'bind'):
        entries = __wrap_as_list(entries)
        for bind_entry in entries:
            if '@type' in bind_entry:
                xpath = bind_entry.get('@nodeset')
                schema[xpath]['type'] = bind_entry.get('@type')
                schema[xpath]['required'] = bind_entry.get('@required') == 'true()'

    # search in body all the repeat entries
    for entries in __find_in_dict(xform_dict, 'repeat'):
        entries = __wrap_as_list(entries)
        for repeat_entry in entries:
            xpath = repeat_entry.get('@nodeset')
            schema[xpath]['type'] = 'repeat'

    return schema


def __get_xform_itexts(xform_dict):
    '''
    Extract all translated texts from xForm definition (as dict)

    <itext>
        <translation default="true()" lang="AAA">
            <text id="/Form/field/one:label">
                <value>One</value>
            </text>
            <text id="/Form/field/two:label">
                <value form="image">jr://images/two.png</value>
                <value>Two</value>
            </text>
            ...
        </translation>
        <translation lang="BBB">
            ...
        </translation>
    </itext>
    '''

    try:
        model = xform_dict['h:html']['h:head']['model']
        translations = __wrap_as_list(model['itext']['translation'])
    except Exception:
        # translations are not mandatory
        return {}

    # the first translation entry must be the default language
    translation = translations[0]  # take the first one
    # just in case check the whole list
    for tt in translations:
        if tt.get('@default') == 'true()':
            translation = tt
            break

    # convert all text entries in a dict wich key is the text id
    itexts = {}
    for text_entry in __wrap_as_list(translation.get('text')):
        for value in __wrap_as_list(text_entry.get('value')):
            if isinstance(value, str):
                itexts[text_entry.get('@id')] = value
                break
    return itexts


def __get_xform_label(xform_dict, xpath, texts={}):
    '''
    Searches the "label" tag linked to the xpath in the xForm definition.
    If not found returns the xpath.
    '''

    # remove root in xpath (it's not going to be sent in the submission)
    label = '/' + '/'.join(xpath.split('/')[2:])
    try:
        body = xform_dict['h:html']['h:body'] or {}
    except Exception:
        # this should never happen because we already validated the xForm
        # but in the test we are checking all the possible cases trying to break this
        return label

    tags = list(__find_by_key_value(body, key='@ref', value=xpath))
    if not tags:
        return label

    tag = tags[0]  # there is only one
    if not tag.get('label'):
        return label

    label_tag = tag.get('label')
    if isinstance(label_tag, str):
        return label_tag

    ref = label_tag.get('@ref')
    if ref and ref.startswith("jr:itext('") and ref.endswith("')"):
        #   <label ref="jr:itext('{xpath}:label')"/>
        label_id = ref[10:-2]  # f'{xpath}:label'
        if label_id in texts and texts[label_id]:
            return texts[label_id]

    return label


def __get_avro_primitive_type(xform_type, required=False):
    '''
    Transforms the xForm data type into its equivalent AVRO primitive type.
    '''

    AVRO_TYPES = (
        # 'boolean',  # not supported by ODK Collect
        # 'bytes',    # it's equivalent to binary, will contain the file path to the content
        'double',
        'float',
        'int',
        'long',
        'string',
    )

    if xform_type in ('integer', 'short'):
        _type = 'int'
    elif xform_type == 'decimal':
        _type = 'double'
    elif xform_type in ('select', 'select1'):
        _type = 'string'
    elif xform_type not in AVRO_TYPES:  # what to do with an unknown type
        _type = 'string'
    else:
        _type = xform_type

    if not required:
        _type = ['null', _type]

    return _type


def __validate_avro_schema(avro_schema):  # pragma: no cover
    # apart from naming errors, are we generating an invalid schema???
    try:
        parse_avro_schema(json.dumps(avro_schema))
    except SchemaParseException as e:
        avro_schema['_errors'].append(str(e))


def __validate_avro_name(name):
    if _RE_AVRO_NAME.match(name) is None:
        raise SchemaParseException(f'Invalid name "{name}".')


# ------------------------------------------------------------------------------
# Private helper methods
# ------------------------------------------------------------------------------

def __wrap_as_list(value):
    if not isinstance(value, list):
        return [value]
    return value


def __delete_key_in_dict(dictionary, key):
    def walk(obj):
        if isinstance(obj, dict):
            if key in obj:
                del obj[key]
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(dictionary)


def __find_in_dict(dictionary, key):
    # https://gist.github.com/douglasmiranda/5127251
    for k, v in dictionary.items():
        if k == key:
            yield v

        # continue searching in the value
        for result in __iterate_dict(v, __find_in_dict, key):
            yield result


def __find_by_key_value(dictionary, key, value):
    for k, v in dictionary.items():
        if k == key and v == value:
            yield dictionary

        # continue searching in the value keys
        for result in __iterate_dict(v, __find_by_key_value, key, value):
            yield result


def __iterate_dict(value, func, *args, **kwargs):
    if isinstance(value, dict):
        for result in func(value, *args, **kwargs):
            yield result

    elif isinstance(value, list):
        for d in value:
            if isinstance(d, dict):
                for result in func(d, *args, **kwargs):
                    yield result


def __get_all_paths(dictionary):
    '''
    Returns the list of jsonpaths with a boolean indicating if the jsonpath
    corresponds to an intermediate field (has children).

    It does not return any attribute paths.

    It's only used to get the jsonpaths (or xpaths)
    of the instance skeleton defined in the xForm.

    Assumption: there are no lists in the skeleton.
    '''
    def walk(obj, parent_keys=[]):
        for k, v in obj.items():
            if k.startswith('@'):  # ignore attributes
                continue
            keys = parent_keys + [k]
            xpath = '/' + '/'.join(keys)
            paths.append((xpath, isinstance(v, dict)))
            if isinstance(v, dict):
                walk(v, keys)

    paths = []
    walk(dictionary)
    return paths


# https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary-in-python
def __etree_to_dict(elem):
    # this method is not perfect but it's enough for us
    def clean(name):
        for uri, prefix in ElementTree.register_namespace._namespace_map.items():
            pref = f'{prefix}:' if prefix else ''
            name = name.replace('{%s}' % uri, pref)
        return name

    tt = clean(elem.tag)
    d = {tt: {} if elem.attrib else None}
    children = list(elem)

    if children:
        dd = defaultdict(list)
        for dc in map(__etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {tt: {clean(k): v[0] if len(v) == 1 else v for k, v in dd.items()}}

    if elem.attrib:
        d[tt].update(('@' + clean(k), v) for k, v in elem.attrib.items())

    if elem.text:
        text = elem.text.strip()
        if children or elem.attrib:
            if text:
                d[tt]['#text'] = text
        else:
            d[tt] = text
    return d
