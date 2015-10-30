import pytest

from xml.dom.minidom import parseString

from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite

from django.test import Client

from .models import FormTemplate
from .admin import FormTemplateAdmin

TEST_FORM = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:jr="http://openrosa.org/javarosa">
  <h:head>
    <h:title>My Form</h:title>
    <model>
      <instance>
        <data id="build_My-Form_1445334473">
          <meta>
            <instanceID/>
          </meta>
          <untitled9/>
          <untitled10/>
        </data>
      </instance>
      <itext>
        <translation lang="eng">
          <text id="/data/untitled10:label">
            <value>Welcome!</value>
          </text>
          <text id="/data/untitled10:option0">
            <value>Tea</value>
          </text>
          <text id="/data/untitled10:option1">
            <value>Coffee</value>
          </text>
        </translation>
      </itext>
      <bind nodeset="/data/meta/instanceID" type="string" readonly="true()" calculate="concat('uuid:', uuid())"/>
      <bind nodeset="/data/untitled9" type="string"/>
      <bind nodeset="/data/untitled10" type="select1" required="true()"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/data/untitled9">
    </input>
    <select1 ref="/data/untitled10">
      <label ref="jr:itext('/data/untitled10:label')"/>
      <item>
        <label ref="jr:itext('/data/untitled10:option0')"/>
        <value>tea</value>
      </item>
      <item>
        <label ref="jr:itext('/data/untitled10:option1')"/>
        <value>coffee</value>
      </item>
    </select1>
  </h:body>
</h:html>
"""


class MockFile(object):

    def read(self):
        return TEST_FORM


class MockRequest(object):
    FILES = {
        'upload': MockFile()
    }


class MockSuperUser(object):

    def has_perm(self, perm):
        return True


@pytest.mark.django_db
def test_formtemplate():
    a = FormTemplate(id=12, name="A name")
    assert str(a) == "12 - A name"


@pytest.mark.django_db
def test_get_formlist():
    username = 'test'
    email = 'test@example.com'
    password = 'test'

    u = User.objects.create_superuser(username, email, password)

    fta = FormTemplateAdmin(FormTemplate, AdminSite())

    a = FormTemplate(
        created_by=u,
        name="A test form",
    )

    request = MockRequest()
    request.user = u

    fta.save_model(
        request, a,
    )

    client = Client()
    response = client.get("/odk/formList")

    assert response.status_code == 200
    assert response.content.decode('utf-8') == """<?xml version="1.0" encoding="utf-8"?>
<xforms xmlns="http://openrosa.org/xforms/xformsList"><xform><formID>1</formID><name>A test form</name><descriptionText></descriptionText><downloadUrl>http://testserver/odk/form/1/</downloadUrl></xform></xforms>"""

    assert response.has_header('x-openrosa-accept-content-length')
    assert response.has_header('x-openrosa-version')

    xmldoc = parseString(response.content.decode('utf-8'))

    formUrl = [
        n
        for n
        in xmldoc.documentElement.firstChild.childNodes
        if n.tagName == 'downloadUrl'
    ][0].firstChild.wholeText

    response = client.get(formUrl)

    assert response.status_code == 200
    assert 'nodeset="/data/meta/instanceID"' in response.content.decode('utf-8')
    assert response.has_header('x-openrosa-accept-content-length')
    assert response.has_header('x-openrosa-version')
