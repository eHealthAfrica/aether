import base64

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from ..models import XForm


UserModel = get_user_model().objects

XFORM_XLS_FILE = '/code/api/tests/files/demo-xform.xls'
XFORM_XML_FILE = '/code/api/tests/files/demo-xform.xml'

XML_DATA_FILE = '/code/api/tests/files/demo-data.xml'
XML_DATA_FILE_ERR = '/code/api/tests/files/demo-data--error.xml'

XML_DATA = '''
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
            <None id="xform-id-test">
              <starttime/>
              <endtime/>
              <deviceid/>
              <meta>
                <instanceID/>
              </meta>
            </None>
          </instance>
          <instance id="other-entry">
          </instance>
        </model>
      </h:head>
      <h:body>
      </h:body>
    </h:html>
'''

XML_DATA_ERR = '''
    <h:html
        xmlns="http://www.w3.org/2002/xforms"
        xmlns:ev="http://www.w3.org/2001/xml-events"
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:jr="http://openrosa.org/javarosa"
        xmlns:orx="http://openrosa.org/xforms"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">

      <h:head>
'''


class CustomTestCase(TransactionTestCase):

    def setUp(self):
        with open(XFORM_XML_FILE, 'r') as f:
            XFORM_XML_RAW = f.read()

        self.samples = {
            # sample collection for submission posts
            'submission': {
                'file-ok': XML_DATA_FILE,
                'file-err': XML_DATA_FILE_ERR,
            },

            # sample collection for xForm objects
            'xform': {
                'xml-ok': XML_DATA,
                'xml-err': XML_DATA_ERR,

                'raw-xml': XFORM_XML_RAW,
                'file-xls': XFORM_XLS_FILE,
                'file-xml': XFORM_XML_FILE,
            },
        }

    def tearDown(self):
        self.client.logout()

    def helper_create_superuser(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        basic = b'admin:adminadmin'

        self.admin = UserModel.create_superuser(username, email, password)
        self.headers_admin = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(basic).decode('ascii')
        }
        self.assertTrue(self.client.login(username=username, password=password))

    def helper_create_user(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        basic = b'test:testtest'

        self.user = UserModel.create_user(username, email, password)
        self.headers_user = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(basic).decode('ascii')
        }

    def helper_create_surveyor(self, username='surveyor'):
        email = username + '@example.com'
        password = 'surveyorsurveyor'
        surveyor = UserModel.create_user(username, email, password)
        surveyor.first_name = 'surveyor'
        surveyor.save()
        return surveyor

    def helper_create_xform(self, surveyor=None, survey_id=1):
        xform = XForm.objects.create(
            description='test',
            gather_core_survey_id=survey_id,
            xml_data=self.samples['xform']['raw-xml'],
        )

        if surveyor:
            xform.surveyors.add(surveyor)
            xform.save()

        return xform
