from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from . import CustomTestCase

from ..xform_utils import (
    extract_data_from_xml,
    parse_submission,
    parse_xmlform,
    validate_xmldict,
    get_instance_id,
)


class XFormUtilsTests(CustomTestCase):

    def test__validate_xmldict_no_title(self):
        self.assertRaises(
            ValidationError,
            validate_xmldict,
            '''
                <h:html>
                  <h:head>
                    <model>
                      <instance>
                      </instance>
                    </model>
                  </h:head>
                  <h:body>
                  </h:body>
                </h:html>
            '''
        )

    def test__validate_xmldict_empty_title(self):
        self.assertRaises(
            ValidationError,
            validate_xmldict,
            '''
                <h:html>
                  <h:head>
                    <h:title></h:title>
                    <model>
                      <instance id="xform-id-test">
                      </instance>
                    </model>
                  </h:head>
                  <h:body>
                  </h:body>
                </h:html>
            '''
        )

    def test__validate_xmldict_no_xform_id(self):
        self.assertRaises(
            ValidationError,
            validate_xmldict,
            '''
                <h:html>
                  <h:head>
                    <h:title>xForm - Test</h:title>
                    <model>
                      <instance>
                      </instance>
                      <instance>
                        <None></None>
                      </instance>
                    </model>
                  </h:head>
                  <h:body>
                  </h:body>
                </h:html>
            '''
        )

    def test__validate_xmldict_empty_xform_id(self):
        self.assertRaises(
            ValidationError,
            validate_xmldict,
            '''
                <h:html>
                  <h:head>
                    <h:title>xForm - Test</h:title>
                    <model>
                      <instance id="">
                      </instance>
                    </model>
                  </h:head>
                  <h:body>
                  </h:body>
                </h:html>
            '''
        )

    def test__parse_xml(self):
        # edge case, xml contains empty tags
        xml_content = '<?xml version="1.0" ?> <tag1><tag attr="1"/>text<tag attr="2"/></tag1>'
        xml_file = SimpleUploadedFile('xform.xml', bytes(xml_content, encoding='utf-8'))
        self.assertEqual(parse_xmlform(xml_file), xml_content, 'it returns the same content')

    def test__parse_submission(self):
        with open(self.samples['submission']['file-ok'], 'rb') as xml:
            data, form_id, version = extract_data_from_xml(xml)

        self.assertEqual(form_id, 'my-test-form')
        self.assertEqual(version, '0')
        self.assertEqual(len(list(data.keys())), 1)
        self.assertEqual(list(data.keys())[0], 'Something_that_is_not_None')

        data = parse_submission(data, self.samples['xform']['raw-xml'])

        self.assertNotEqual(list(data.keys())[0], 'Something_that_is_not_None')

    def test__get_instance_id(self):
        instance_id = 'abc'
        valid_data = {'meta': {'instanceID': instance_id}}
        result = get_instance_id(valid_data)
        self.assertEqual(result, instance_id)
        invalid_data = {}
        result = get_instance_id(invalid_data)
        self.assertIsNone(result)
