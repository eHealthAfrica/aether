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

import json

from . import CustomTestCase
from ..xform_utils import (
    __get_all_paths as get_paths,
    __get_avro_primitive_type as get_type,
    __get_xform_instance as get_instance,
    __get_xform_itexts as get_texts,
    __get_xform_label as get_label,
    __parse_xml_to_dict as parse_xml_to_dict,

    get_instance_data_from_xml,
    get_instance_id,

    parse_submission,
    parse_xform_file,
    parse_xform_to_avro_schema,

    validate_xform,
)


class XFormUtilsValidatorsTests(CustomTestCase):

    def test__validate_xform__not_valid(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(self.samples['xform']['xml-err'])
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'not valid xForm definition')

    def test__validate_xform__missing_required(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head/>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing required tags', ve)

    def test__validate_xform__no_instance(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head>
                            <h:title/>
                            <model>
                                <instance>
                                </instance>
                                <bind/>
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing instance definition')

    def test__validate_xform__no_title__no_form_id(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head>
                            <h:title/>
                            <model>
                                <instance>
                                    <A/>
                                </instance>
                                <bind/>
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing title and form_id')

    def test__validate_xform__no_title__blank(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head>
                            <h:title/>
                            <model>
                                <instance>
                                    <B id="xform-id-test"/>
                                </instance>
                                <bind />
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing title')

    def test__validate_xform__no_xform_id(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head>
                            <h:title>xForm - Test</h:title>
                            <model>
                                <instance>
                                    <None/>
                                </instance>
                                <bind />
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing form_id')

    def test__validate_xform__no_xform_id__blank(self):
        with self.assertRaises(TypeError) as ve:
            validate_xform(
                '''
                    <h:html
                            xmlns="http://www.w3.org/2002/xforms"
                            xmlns:ev="http://www.w3.org/2001/xml-events"
                            xmlns:h="http://www.w3.org/1999/xhtml"
                            xmlns:jr="http://openrosa.org/javarosa"
                            xmlns:orx="http://openrosa.org/xforms"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <h:head>
                            <h:title>xForm - Test</h:title>
                            <model>
                                <instance>
                                    <C id=""/>
                                </instance>
                                <bind />
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing form_id')

    def test__validate_xform__with__title__and__xform_id(self):
        try:
            validate_xform(self.samples['xform']['xml-ok'])
            self.assertTrue(True)
        except TypeError as ve:
            self.assertIsNone(ve)
            self.assertTrue(False)


class XFormUtilsParsersTests(CustomTestCase):

    def test__parse_xml_to_dict(self):
        xml_str = '''
            <root attr="a">
                <!-- Comments are ignored -->
                <a>
                    Some text
                    <!-- It does not parse values, everything is a string -->
                    <b>1</b>
                </a>
                <a>
                    <b/>
                </a>
                <a>
                    Some text
                    <b>1</b>
                    More text (and IT'S IGNORED!!!)
                </a>
                <!-- This tag below will appear as a None value -->
                <a/>
            </root>
        '''
        expected = {
            'root': {
                '@attr': 'a',
                'a': [
                    {
                        '#text': 'Some text',
                        'b': '1',
                    },
                    {
                        'b': None,
                    },
                    {
                        '#text': 'Some text',
                        'b': '1',
                    },
                    None,  # Oh!
                ]
            }
        }
        self.assertEqual(parse_xml_to_dict(xml_str), expected)

    def test__parse_xform_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as fp:
            xls_content = parse_xform_file('xform.xls', fp)
        with open(self.samples['xform']['file-xml'], 'rb') as fp:
            xml_content = parse_xform_file('xform.xml', fp)

        self.assertEqual(
            parse_xml_to_dict(xls_content),
            parse_xml_to_dict(xml_content),
            'The XLS form and the XML form should define both the same form'
        )

    def test__parse_submission(self):
        with open(self.samples['submission']['file-ok'], 'rb') as xml:
            data, form_id, version = get_instance_data_from_xml(xml.read())
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            expected = json.load(content)

        self.assertEqual(form_id, 'my-test-form')
        self.assertEqual(version, 'test-1.0')
        self.assertEqual(len(list(data.keys())), 1)
        self.assertEqual(list(data.keys())[0], 'Something_that_is_not_None')

        data = parse_submission(data, self.samples['xform']['raw-xml'])
        self.assertNotEqual(list(data.keys())[0], 'Something_that_is_not_None')

        self.assertEqual(data, expected)

    def test__parse_submission__with_multilanguage(self):
        with open(self.samples['submission']['file-ok'], 'rb') as xml:
            data, form_id, version = get_instance_data_from_xml(xml.read())
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            expected = json.load(content)

        self.assertEqual(form_id, 'my-test-form')
        self.assertEqual(version, 'test-1.0')
        self.assertEqual(len(list(data.keys())), 1)
        self.assertEqual(list(data.keys())[0], 'Something_that_is_not_None')

        # this form definition has more than one language declared
        data = parse_submission(data, self.samples['xform']['raw-xml-i18n'])
        self.assertNotEqual(list(data.keys())[0], 'Something_that_is_not_None')

        self.assertEqual(data, expected)


class XFormUtilsGettersTests(CustomTestCase):

    def test__get_instance_id(self):
        instance_id = 'abc'
        valid_data = {'meta': {'instanceID': instance_id}}
        result = get_instance_id(valid_data)
        self.assertEqual(result, instance_id)
        invalid_data = {}
        result = get_instance_id(invalid_data)
        self.assertIsNone(result)


class XFormUtilsAvroTests(CustomTestCase):

    def test__get_all_paths(self):
        self.assertEqual(get_paths({}), [])
        self.assertEqual(get_paths({'@a': 0}), [])
        self.assertEqual(get_paths({'a': 0}), [('/a', False)])
        self.assertEqual(get_paths({'a': {'b': 0}}), [('/a', True), ('/a/b', False)])
        self.assertEqual(
            get_paths({'a': {'b': 0, 'c': 0}}),
            [('/a', True), ('/a/b', False), ('/a/c', False)])

    def test__get_avro_type__not_required(self):
        # avro types
        self.assertEqual(get_type('boolean'), ['null', 'string'])
        self.assertEqual(get_type('bytes'), ['null', 'string'])
        self.assertEqual(get_type('double'), ['null', 'double'])
        self.assertEqual(get_type('float'), ['null', 'float'])
        self.assertEqual(get_type('int'), ['null', 'int'])
        self.assertEqual(get_type('long'), ['null', 'long'])
        self.assertEqual(get_type('string'), ['null', 'string'])

        # xform specific types
        self.assertEqual(get_type('binary'), ['null', 'string'])
        self.assertEqual(get_type('date'), ['null', 'string'])
        self.assertEqual(get_type('dateTime'), ['null', 'string'])
        self.assertEqual(get_type('decimal'), ['null', 'double'])
        self.assertEqual(get_type('integer'), ['null', 'int'])
        self.assertEqual(get_type('select'), ['null', 'string'])
        self.assertEqual(get_type('select1'), ['null', 'string'])
        self.assertEqual(get_type('short'), ['null', 'int'])

        # unknown
        self.assertEqual(get_type('any-type'), ['null', 'string'])

    def test__get_avro_type__required(self):
        # avro types
        self.assertEqual(get_type('boolean', True), 'string')
        self.assertEqual(get_type('bytes', True), 'string')
        self.assertEqual(get_type('double', True), 'double')
        self.assertEqual(get_type('float', True), 'float')
        self.assertEqual(get_type('int', True), 'int')
        self.assertEqual(get_type('long', True), 'long')
        self.assertEqual(get_type('string', True), 'string')

        # xform specific types
        self.assertEqual(get_type('binary', True), 'string')
        self.assertEqual(get_type('date', True), 'string')
        self.assertEqual(get_type('dateTime', True), 'string')
        self.assertEqual(get_type('decimal', True), 'double')
        self.assertEqual(get_type('integer', True), 'int')
        self.assertEqual(get_type('select', True), 'string')
        self.assertEqual(get_type('select1', True), 'string')
        self.assertEqual(get_type('short', True), 'int')

        # unknown
        self.assertEqual(get_type('any-type', True), 'string')

    def test__get_xform_instance__error(self):
        with self.assertRaises(TypeError) as ve:
            get_instance({})
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing instance definition')

    def test__get_xform_instance__error__no_instances(self):
        with self.assertRaises(TypeError) as ve:
            get_instance({
                'h:html': {
                    'h:head': {
                        'model': {
                            'instance': {}
                        }
                    }
                }
            })
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing instance definition')

    def test__get_xform_instance__error___no_default_instance(self):
        with self.assertRaises(TypeError) as ve:
            get_instance({
                'h:html': {
                    'h:head': {
                        'model': {
                            'instance': [
                                {'@id': 1},
                                {'@id': 2},
                                {'@id': 3},
                            ]
                        }
                    }
                }
            })
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing instance definition')

    def test__get_xform_instance(self):
        xform_dict = {
            'h:html': {
                'h:head': {
                    'model': {
                        'instance': [
                            {'@id': 1},
                            {'@id': 2},
                            {'root': {'content': 1}},
                            {'@id': 3},
                        ]
                    }
                }
            }
        }
        self.assertEqual(get_instance(xform_dict, False), {'content': 1})
        self.assertEqual(get_instance(xform_dict, True), {'root': {'content': 1}})

    def test__get_xform_itexts__no_texts(self):
        xform_dict = {'h:html': {'h:head': {'model': {}}}}
        self.assertEqual(get_texts(xform_dict), {})

    def test__get_xform_itexts__one_language(self):
        xform_dict = {
            'h:html': {
                'h:head': {
                    'model': {
                        'itext': {
                            'translation': {
                                # this should always be there,
                                # but check that at least takes the first one
                                # '@default': 'true()',
                                '@lang': 'AA',
                                'text': {
                                    '@id': 'a',
                                    'value': 'A',
                                }
                            }
                        }
                    }
                }
            }
        }
        self.assertEqual(get_texts(xform_dict), {'a': 'A'})

    def test__get_xform_itexts__multi_language(self):
        xform_dict = {
            'h:html': {
                'h:head': {
                    'model': {
                        'itext': {
                            'translation': [
                                {
                                    '@lang': 'AA',
                                    'text': [{
                                        '@id': 'a',
                                        'value': 'A',
                                    }]
                                },
                                {
                                    '@default': 'true()',
                                    '@lang': 'BB',
                                    'text': [{
                                        '@id': 'a',
                                        'value': 'B',
                                    }]
                                },
                            ]
                        }
                    }
                }
            }
        }
        self.assertEqual(get_texts(xform_dict), {'a': 'B'})

    def test__get_xform_label__no_body(self):
        xform_dict = {'h:html': {'h:body': None}}
        self.assertEqual(get_label(xform_dict, '/None'), '/', 'removes root')
        self.assertEqual(get_label(xform_dict, '/None/any'), '/any')

    def test__get_xform_label__no_linked_label(self):
        xform_dict = {
            'h:html': {
                'h:body': {
                    'any-tag': {
                        '@ref': '/None/any',
                    }
                }
            }
        }
        self.assertEqual(get_label(xform_dict, '/None/any'), '/any')

    def test__get_xform_label__blank_label(self):
        xform_dict = {
            'h:html': {
                'h:body': {
                    'any-tag': {
                        '@ref': '/None/any',
                        'label': '',
                    }
                }
            }
        }
        self.assertEqual(get_label(xform_dict, '/None/any'), '/any')

    def test__get_xform_label__one_language(self):
        xform_dict = {
            'h:html': {
                'h:body': {
                    'any-tag': {
                        '@ref': '/None/any',
                        'label': 'Any',
                    }
                }
            }
        }
        self.assertEqual(get_label(xform_dict, '/None/any'), 'Any')

    def test__get_xform_label__multi_language(self):
        xform_dict = {
            'h:html': {
                'h:body': {
                    'any-tag': {
                        '@ref': '/None/a/b/c/any',
                        'label': {
                            '@ref': 'jr:itext(\'any:label\')',
                        },
                    }
                }
            }
        }
        self.assertEqual(get_label(xform_dict, '/None/a/b/c/any'), '/a/b/c/any')
        self.assertEqual(
            get_label(xform_dict, '/None/a/b/c/any', {'any:label': 'Something'}),
            'Something'
        )

    def test__parse_xform_to_avro_schema__with_multilanguage(self):
        with open(self.samples['xform']['file-avro'], 'rb') as content:
            xform_avro = json.load(content)

        schema = parse_xform_to_avro_schema(self.samples['xform']['raw-xml'])
        self.assertEqual(schema['name'], 'MyTestForm')
        self.assertEqual(schema['doc'], 'My Test Form (id: my-test-form, version: Test-1.0)')

        self.assertEqual(schema, xform_avro)

        schema_i18n = parse_xform_to_avro_schema(self.samples['xform']['raw-xml-i18n'])
        self.assertEqual(schema_i18n['name'], 'MyTestForm')
        self.assertEqual(schema_i18n['doc'], 'My Test Form (multilang) (id: my-test-form, version: Test-1.0)')

        # the same fields
        self.assertEqual(schema['fields'], schema_i18n['fields'])

    def test__parse_xform_to_avro_schema__nested_repeats(self):
        xml_definition = '''
            <h:html
                    xmlns="http://www.w3.org/2002/xforms"
                    xmlns:ev="http://www.w3.org/2001/xml-events"
                    xmlns:h="http://www.w3.org/1999/xhtml"
                    xmlns:jr="http://openrosa.org/javarosa"
                    xmlns:odk="http://www.opendatakit.org/xforms"
                    xmlns:orx="http://openrosa.org/xforms"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <h:head>
                    <h:title>nested repeats test</h:title>
                    <model>
                        <instance>
                            <nested-repeats id="nested_repeats_test">
                                <Repeat_1 jr:template="">
                                    <name/>
                                    <Repeat_2 jr:template="">
                                        <name2/>
                                    </Repeat_2>
                                </Repeat_1>
                                <meta>
                                    <instanceID/>
                                </meta>
                            </nested-repeats>
                        </instance>

                        <bind nodeset="/nested-repeats/Repeat_1/name" type="string"/>
                        <bind nodeset="/nested-repeats/Repeat_1/Repeat_2/name2" type="string"/>
                        <bind
                                calculate="concat('uuid:', uuid())"
                                nodeset="/nested-repeats/meta/instanceID"
                                readonly="true()"
                                type="string"/>
                    </model>
                </h:head>
                <h:body class="pages">
                    <group ref="/nested-repeats/Repeat_1">
                        <label></label>
                        <repeat nodeset="/nested-repeats/Repeat_1">
                            <input ref="/nested-repeats/Repeat_1/name">
                                <label>name_label</label>
                            </input>
                            <group ref="/nested-repeats/Repeat_1/Repeat_2">
                                <label></label>
                                <repeat nodeset="/nested-repeats/Repeat_1/Repeat_2">
                                    <input ref="/nested-repeats/Repeat_1/Repeat_2/name2">
                                        <label>name_label</label>
                                    </input>
                                </repeat>
                            </group>
                        </repeat>
                    </group>
                </h:body>
            </h:html>
        '''

        expected = {
            'name': 'NestedRepeatsTest',
            'namespace': 'aether.odk.xforms',
            'doc': 'nested repeats test (id: nested_repeats_test, version: 0)',
            'type': 'record',
            'fields': [
                {
                    'name': '_id',
                    'doc': 'xForm ID',
                    'type': 'string',
                    'default': 'nested_repeats_test',
                },
                {
                    'name': '_version',
                    'doc': 'xForm version',
                    'type': 'string',
                    'default': '0',
                },
                {
                    'name': 'Repeat_1',
                    'type': {
                        'type': 'array',
                        'items': {
                            'name': 'Repeat_1',
                            'doc': '/Repeat_1',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'name',
                                    'type': [
                                        'null',
                                        'string',
                                    ],
                                    'doc': 'name_label',
                                },
                                {
                                    'name': 'Repeat_2',
                                    'type': {
                                        'type': 'array',
                                        'items': {
                                            'name': 'Repeat_2',
                                            'doc': '/Repeat_1/Repeat_2',
                                            'type': 'record',
                                            'fields': [
                                                {
                                                    'name': 'name2',
                                                    'type': [
                                                        'null',
                                                        'string',
                                                    ],
                                                    'doc': 'name_label',
                                                },
                                            ],
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
                {
                    'name': 'meta',
                    'type': {
                        'name': 'meta',
                        'doc': '/meta',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'instanceID',
                                'type': [
                                    'null',
                                    'string'
                                ],
                                'doc': '/meta/instanceID',
                            },
                        ],
                    },
                }
            ],
        }

        self.assertEqual(parse_xform_to_avro_schema(xml_definition), expected)
