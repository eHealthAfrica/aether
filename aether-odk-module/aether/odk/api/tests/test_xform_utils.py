from django.core.exceptions import ValidationError

from . import CustomTestCase

from ..xform_utils import validate_xmldict


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
