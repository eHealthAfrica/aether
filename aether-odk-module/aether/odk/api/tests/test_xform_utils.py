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
    get_instance_data_from_xml,
    get_instance_id,
    parse_submission,
    parse_file,
    validate_xform,
    __parse_xml_to_dict as parse_xml_to_dict
)


class XFormUtilsTests(CustomTestCase):

    def test__validate_xform__not_valid(self):
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
        self.assertEqual(str(ve.exception), 'not valid xForm definition')

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
                            <model>
                                <bind/>
                            </model>
                        </h:head>
                        <h:body/>
                    </h:html>
                '''
            )
        self.assertIsNotNone(ve)
        self.assertEqual(str(ve.exception), 'missing instance definition')

    def test__validate_xform__none_instance(self):
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
                            <model>
                                <instance/>
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

    def test__validate_xform__no_title(self):
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
                            <model>
                                <instance>
                                    <A id="xform-id-test"/>
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
                            <h:title></h:title>
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

    def test__parse_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as fp:
            xls_content = parse_file('xform.xls', fp)
        with open(self.samples['xform']['file-xml'], 'rb') as fp:
            xml_content = parse_file('xform.xml', fp)

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

    def test__get_instance_id(self):
        instance_id = 'abc'
        valid_data = {'meta': {'instanceID': instance_id}}
        result = get_instance_id(valid_data)
        self.assertEqual(result, instance_id)
        invalid_data = {}
        result = get_instance_id(invalid_data)
        self.assertIsNone(result)
