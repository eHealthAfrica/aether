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

import re
import xmltodict

from dateutil import parser

from pyxform import xls2json, builder
from pyxform.xls2json_backends import xls_to_dict

from django.core.exceptions import ValidationError


def parse_file(filename, content):
    if filename.endswith('.xml'):
        return parse_xmlform(content)
    else:
        return parse_xlsform(content)


def parse_xlsform(fp):
    warnings = []
    json_survey = xls2json.workbook_to_json(xls_to_dict(fp), None, 'default', warnings)
    survey = builder.create_survey_element_from_dict(json_survey)
    return survey.xml().toprettyxml(indent='  ')


def parse_xmlform(fp):
    content = fp.read()
    # check that the file content is a valid XML
    xmltodict.parse(content)
    # but return the untouched content if it does not raise an exception
    return content.decode('utf-8')


def get_xml_title(data):
    '''
    Extracts form title from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            ...
          </h:head>
          <h:body>
          </h:body>
        </h:html>

     '''

    try:
        # data is an `OrderedDict` object
        return data['h:html']['h:head']['h:title']
    except Exception:
        return None


def get_xml_form_id(data):
    '''
    Extracts form id from xml definition
    '''

    return get_xml_instance_attr(data, '@id')


def get_xml_version(data):
    '''
    Extracts form version from xml definition
    '''

    return get_xml_instance_attr(data, '@version')


def get_xml_instance_attr(data, attr):
    '''
    Extracts the attribute of the first instance child from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <instance>
                <Something id="F O R M I D" version="V E R S I O N"></Something>
              </instance>
              <instance id="choice-1"></instance>
              <instance id="choice-2"></instance>

              <instance id="choice-n"></instance>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>

    '''

    try:
        # data is an `OrderedDict` object
        instance = data['h:html']['h:head']['model']['instance']
        # this can be a list of instances or one entry
        if isinstance(instance, list):
            # assumption: the first one is the form definition, the rest are the choices
            instance = instance[0]

        if isinstance(instance, dict):
            # assumption: there is only one child (key)
            key = list(instance.keys())[0]
            return instance[key][attr]

    except Exception:
        pass

    return None


def validate_xmldict(value):
    '''
    Validates xml definition:

    1. parses xml
    2. checks if title is valid
    3. checks if form id is valid

    '''

    try:
        data = xmltodict.parse(value)

        if not get_xml_title(data):
            raise ValidationError('missing title')
        if not get_xml_form_id(data):
            raise ValidationError('missing form_id')

    except Exception as e:
        raise ValidationError(e)


def extract_data_from_xml(xml):
    '''
    Parses the XML submission file into a dictionary,
    also extracts the form id and the form version.
    '''

    data = xmltodict.parse(xml.read())

    instance = list(data.items())[0][1]  # TODO make more robust
    form_id = instance['@id']
    version = instance['@version'] if '@version' in instance else '0'

    return data, form_id, version


def get_instance_id(data):
    '''
    Extracts device instance id from xml data
    '''

    try:
        return data['meta']['instanceID']
    except Exception:
        return None


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

    def walk(obj, parent_keys, coerce_dict):
        if not parent_keys:
            parent_keys = []

        for k, v in obj.items():
            keys = parent_keys + [k]
            xpath = '/' + '/'.join(keys)
            _type = coerce_dict.get(xpath)

            if _type == 'list' and isinstance(v, dict):
                # list of one item but presented as a dict
                # transform it back into a list
                obj[k] = [v]

            if isinstance(v, dict):
                walk(v, keys, coerce_dict)

            elif isinstance(v, list):
                for i in v:
                    # indices are not important
                    walk(i, keys, coerce_dict)

            elif v is not None:
                xpath = '/' + '/'.join(keys)
                _type = coerce_dict.get(xpath)

                if _type in ('int', 'integer'):
                    obj[k] = int(v)

                if _type == 'decimal':
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
                obj[k] = None

    coerce_dict = {}
    # bind entries define the fields and its types or possible values (choices list)
    for bind_entry in re.findall(r'<bind.*/>', xml_definition):
        re_nodeset = re.findall(r'nodeset="([^"]*)"', bind_entry)
        re_type = re.findall(r'type="([^"]*)"', bind_entry)

        try:
            coerce_dict[re_nodeset[0]] = re_type[0]
        except Exception:
            # ignore, sometimes there is no "type"
            # <bind nodeset="/ZZZ/some_field" relevant=" /ZZZ/some_choice ='value'"/>
            pass

    # repeat entries define the "list" fields
    for repeat_entry in re.findall(r'<repeat.*>', xml_definition):
        re_nodeset = re.findall(r'nodeset="([^"]*)"', repeat_entry)
        coerce_dict[re_nodeset[0]] = 'list'

    walk(data, None, coerce_dict)  # modifies inplace

    # assumption: there is only one child that represents the form content
    # usually: {'ZZZ': { ... }}
    # remove this first level and return content
    if len(list(data.keys())) == 1:  # pragma: no cover
        data = data[list(data.keys())[0]]

    return data
