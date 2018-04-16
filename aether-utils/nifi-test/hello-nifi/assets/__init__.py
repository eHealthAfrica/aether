import json
import os

kernel_url = "http://kernel:8000"

kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

def file_to_json(path):
    with open(path) as f:
        return json.load(f)

here = os.path.dirname(os.path.realpath(__file__))

project_name = "HFRDemo"
project_obj = {
    "revision": "1",
    "name": project_name,
    "salad_schema": "{}",
    "jsonld_context": "[]",
    "rdf_definition": "[]"
}

definition = file_to_json("%s/%s" % (here, "SimpleClinic.json"))
schema_obj = {
    "name": "Clinic",
    "type": "record",
    "revision": "1",
    "definition": definition
}

project_schema_obj = {
    "revision": "1",
    "name": "Clinic",
    "masked_fields": "[]",
    "transport_rule": "[]",
    "mandatory_fields": "[]"
}

mapping_def = file_to_json(here+"/mapping.json")
mapping_obj = {
    "name": "hfr",
    "definition": mapping_def,
    "revision": "1"
}
