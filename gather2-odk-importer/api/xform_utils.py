from pyxform import xls2json, builder
from pyxform.xls2json_backends import xls_to_dict
import xmltodict


def parse_xlsform(fp):
    warnings = []
    json_survey = xls2json.workbook_to_json(xls_to_dict(fp), None, 'default', warnings)
    survey = builder.create_survey_element_from_dict(json_survey)
    return survey.xml().toprettyxml(indent='  ')


def parse_xmlform(fp):
    return xmltodict.unparse(xmltodict.parse(fp.read()), pretty=True)
