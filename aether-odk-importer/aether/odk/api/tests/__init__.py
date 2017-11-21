import base64

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from ..models import Survey, XForm
from ..surveyors_utils import get_surveyor_group


UserModel = get_user_model().objects

PATH_DIR = '/code/aether/odk/api/tests/files/'

XFORM_XLS_FILE = PATH_DIR + 'demo-xform.xls'
XFORM_XML_FILE = PATH_DIR + 'demo-xform.xml'

XML_DATA_FILE = PATH_DIR + 'demo-data.xml'
XML_DATA_FILE_ERR = PATH_DIR + 'demo-data--error.xml'

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
        self.surveyor_group = get_surveyor_group()

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
                'file-err': XML_DATA_FILE_ERR,
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
        surveyor.save()
        surveyor.groups.add(self.surveyor_group)
        surveyor.save()
        return surveyor

    def helper_create_survey(self, surveyor=None, mapping_id=1):
        survey, _ = Survey.objects.get_or_create(
            name='test',
            mapping_id=mapping_id,
        )

        if surveyor:
            if type(surveyor) is list:
                survey.surveyors.set(surveyor)
            else:
                survey.surveyors.add(surveyor)
            survey.save()

        return survey

    def helper_create_xform(self, surveyor=None, mapping_id=1):
        xform = XForm.objects.create(
            description='test',
            survey=self.helper_create_survey(
                surveyor=surveyor,
                mapping_id=mapping_id,
            ),
            xml_data=self.samples['xform']['raw-xml'],
        )

        if surveyor:
            if type(surveyor) is list:
                xform.surveyors.set(surveyor)
            else:
                xform.surveyors.add(surveyor)
            xform.save()

        return xform
