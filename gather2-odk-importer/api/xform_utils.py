from django.core.exceptions import ValidationError

from pyxform import xls2json, builder
from pyxform.xls2json_backends import xls_to_dict
import xmltodict


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
    return xmltodict.unparse(xmltodict.parse(fp.read()), pretty=True)


def get_xml_title(data):
    '''
    Extracts form title from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <instance>
                <None id="F O R M I D"></None>
              </instance>
              <instance id="1"></instance>
              <instance id="2"></instance>

              <instance id="n"></instance>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>
     '''
    try:
        return data['h:html']['h:head']['h:title']
    except:
        return None


def get_xml_form_id(data):
    '''
    Extracts form id from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <instance>
                <None id="F O R M I D"></None>
              </instance>
              <instance id="1"></instance>
              <instance id="2"></instance>

              <instance id="n"></instance>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>
    '''
    try:
        instance = data['h:html']['h:head']['model']['instance']
        # this can be a list of intances or one entry
        try:
            return instance['None']['@id']
        except:
            # assumption: the first one is the form definition, the rest are the choices
            return instance[0]['None']['@id']
    except:
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
