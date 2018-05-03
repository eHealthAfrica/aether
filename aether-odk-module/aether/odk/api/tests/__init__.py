import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase

from ..models import Mapping, XForm, MediaFile
from ..surveyors_utils import get_surveyor_group


UserModel = get_user_model().objects

PATH_DIR = '/code/aether/odk/api/tests/files/'

XFORM_XLS_FILE = PATH_DIR + 'demo-xform.xls'
XFORM_XML_FILE = PATH_DIR + 'demo-xform.xml'

XML_DATA_FILE = PATH_DIR + 'demo-data.xml'
XML_DATA_FILE_ERR = PATH_DIR + 'demo-data--error.xml'
XML_DATA_FILE_ERR_MISSING_INSTANCE_ID = PATH_DIR + 'demo-data--error--missing-instance-id.xml'

JSON_DATA_FILE = PATH_DIR + 'demo-data.json'

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
            <Mapping id="xform-id-test" version="v1">
              <starttime/>
              <endtime/>
              <deviceid/>
              <meta>
                <instanceID/>
              </meta>
            </Mapping>
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
                'file-err-missing-instance-id': XML_DATA_FILE_ERR_MISSING_INSTANCE_ID,
                'file-ok-json': JSON_DATA_FILE,
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
        surveyor.groups.add(self.surveyor_group)
        surveyor.save()
        return surveyor

    def helper_create_mapping(self, mapping_id=None, surveyor=None):
        if mapping_id is None:
            mapping_id = uuid.uuid4()

        mapping, _ = Mapping.objects.get_or_create(
            name='test',
            mapping_id=mapping_id,
        )

        self.assertEqual(str(mapping), '{} - test'.format(mapping_id))

        if surveyor:
            if type(surveyor) is list:
                mapping.surveyors.set(surveyor)
            else:
                mapping.surveyors.add(surveyor)
            mapping.save()

        return mapping

    def helper_create_xform(self, mapping_id=None, surveyor=None, with_media=False):
        xform = XForm.objects.create(
            description='test',
            mapping=self.helper_create_mapping(
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

        if with_media:
            MediaFile.objects.create(
                xform=xform,
                media_file=SimpleUploadedFile('sample.txt', b'abc'),
            )

        return xform
