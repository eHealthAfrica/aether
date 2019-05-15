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

import base64
import json
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase

from ..models import Project, XForm, MediaFile
from ..surveyors_utils import get_surveyor_group


UserModel = get_user_model().objects

here = os.path.dirname(os.path.realpath(__file__))
PATH_DIR = os.path.join(here, 'files/')

XFORM_XLS_FILE = PATH_DIR + 'demo-xform.xls'
XFORM_XML_FILE = PATH_DIR + 'demo-xform.xml'
XFORM_XML_FILE_I18N = PATH_DIR + 'demo-xform-multilang.xml'
XFORM_AVRO_FILE = PATH_DIR + 'demo-xform.avsc'

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
                <instance id="other-entry"/>

                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="start"
                        jr:requiredMsg="start"
                        nodeset="/Mapping/starttime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="end"
                        jr:requiredMsg="end"
                        nodeset="/Mapping/endtime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="property"
                        jr:preloadParams="deviceid"
                        jr:requiredMsg="device"
                        nodeset="/Mapping/deviceid"
                        required="true()"
                        type="string"/>

                <bind
                        calculate="concat('uuid:', uuid())"
                        nodeset="/Mapping/meta/instanceID"
                        readonly="true()"
                        type="string"/>
            </model>
        </h:head>
        <h:body/>
    </h:html>
'''

XML_DATA_WITH_ID = '''
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
                    <Mapping id="xform-id-test" version="v2">
                        <starttime/>
                        <endtime/>
                        <deviceid/>
                        <id/>
                        <meta>
                            <instanceID/>
                        </meta>
                    </Mapping>
                </instance>
                <instance id="other-entry"/>

                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="start"
                        jr:requiredMsg="start"
                        nodeset="/Mapping/starttime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="end"
                        jr:requiredMsg="end"
                        nodeset="/Mapping/endtime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="property"
                        jr:preloadParams="deviceid"
                        jr:requiredMsg="device"
                        nodeset="/Mapping/deviceid"
                        required="true()"
                        type="string"/>

                <bind nodeset="/Mapping/id" type="string"/>

                <bind
                        calculate="concat('uuid:', uuid())"
                        nodeset="/Mapping/meta/instanceID"
                        readonly="true()"
                        type="string"/>
            </model>
        </h:head>
        <h:body/>
    </h:html>
'''

XML_DATA_NO_VERSION = '''
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
                    <Mapping id="xform-id-test">
                        <starttime/>
                        <endtime/>
                        <deviceid/>
                        <meta>
                            <instanceID/>
                        </meta>
                    </Mapping>
                </instance>
                <instance id="other-entry"/>

                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="start"
                        jr:requiredMsg="start"
                        nodeset="/Mapping/starttime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="timestamp"
                        jr:preloadParams="end"
                        jr:requiredMsg="end"
                        nodeset="/Mapping/endtime"
                        required="true()"
                        type="dateTime"/>
                <bind
                        jr:preload="property"
                        jr:preloadParams="deviceid"
                        jr:requiredMsg="device"
                        nodeset="/Mapping/deviceid"
                        required="true()"
                        type="string"/>

                <bind
                        calculate="concat('uuid:', uuid())"
                        nodeset="/Mapping/meta/instanceID"
                        readonly="true()"
                        type="string"/>
            </model>
        </h:head>
        <h:body/>
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
        <!-- missing close tag -->
        <h:head>
    </h:html>
'''


class MockResponse:

    def __init__(self, status_code, json_data={}):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json.dumps(json_data).encode('utf-8')

    def json(self):
        return self.json_data


class CustomTestCase(TransactionTestCase):

    def setUp(self):
        self.surveyor_group = get_surveyor_group()

        with open(XFORM_XML_FILE, 'r') as fp:
            XFORM_XML_RAW = fp.read()

        with open(XFORM_XML_FILE_I18N, 'r') as fp:
            XFORM_XML_RAW_I18N = fp.read()

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
                'xml-ok-id': XML_DATA_WITH_ID,
                'xml-ok-noversion': XML_DATA_NO_VERSION,
                'xml-err': XML_DATA_ERR,

                'file-xls': XFORM_XLS_FILE,
                'file-err': XML_DATA_FILE_ERR,

                'raw-xml': XFORM_XML_RAW,
                'file-xml': XFORM_XML_FILE,

                'file-avro': XFORM_AVRO_FILE,

                'raw-xml-i18n': XFORM_XML_RAW_I18N,
                'file-xml-i18n': XFORM_XML_FILE_I18N,
            },
        }

    def tearDown(self):
        self.client.logout()

    def helper_create_uuid(self):
        return uuid.uuid4()

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
        return surveyor

    def helper_create_project(self, project_id=None, surveyor=None):
        if project_id is None:
            project_id = self.helper_create_uuid()

        project, _ = Project.objects.get_or_create(
            name='test',
            project_id=project_id,
        )

        self.assertEqual(str(project), f'{project_id} - test')

        if surveyor:
            if type(surveyor) is list:
                project.surveyors.set(surveyor)
            else:
                project.surveyors.add(surveyor)

        return project

    def helper_create_xform(self,
                            project_id=None,
                            surveyor=None,
                            xml_data=None,
                            with_media=False,
                            with_version=True):
        if not xml_data:
            if with_version:
                xml_data = self.samples['xform']['xml-ok']
            else:
                xml_data = self.samples['xform']['xml-ok-noversion']

        xform = XForm.objects.create(
            description='test',
            project=self.helper_create_project(
                surveyor=surveyor,
                project_id=project_id,
            ),
            xml_data=xml_data,
        )

        if surveyor:
            if type(surveyor) is list:
                xform.surveyors.set(surveyor)
            else:
                xform.surveyors.add(surveyor)

        if with_media:
            MediaFile.objects.create(
                xform=xform,
                media_file=SimpleUploadedFile('sample.txt', b'abc'),
            )

        return xform
