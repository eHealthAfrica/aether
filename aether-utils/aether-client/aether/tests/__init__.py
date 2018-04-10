import json
import os

kernel_url = "http://kernel-test:9000"

kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

odk_credentials ={
    "username": "admin-odk",
    "password": "adminadmin",
}

def file_to_json(path):
    with open(path) as f:
        return json.load(f)

here = os.path.dirname(os.path.realpath(__file__))

#Projects
project_name = "TestProject"
project_def = file_to_json(here+"/fixtures/salad/salad.json")
project_obj = {
    "revision": "1",
    "name": project_name,
    "salad_schema": project_def,
    "jsonld_context": "[]",
    "rdf_definition": "[]"
}

#Schemas
schema_objs = []
schema_dir =here+"/fixtures/avro"
schema_files = os.listdir(schema_dir)


for filename in schema_files:
    name = filename.split(".")[0]
    definition = file_to_json("%s/%s" % (schema_dir, filename))
    schema_obj = {
        "name": "My"+name,
        "type": "record",
        "revision": "1",
        "definition": definition
    }
    schema_objs.append(schema_obj)

schema_names = [fn.split(".")[0] for fn in schema_files]

# ProjectSchemas
project_schema_objs = []
for name in schema_names:
    project_schema_obj = {
        "revision": "1",
        "name": name,
        "masked_fields": "[]",
        "transport_rule": "[]",
        "mandatory_fields": "[]"
    }
    project_schema_objs.append(project_schema_obj)


# Mapping
mapping_def = file_to_json(here+"/fixtures/mappings/form-mapping.json")

mapping_obj = {
    "name": "microcensus",
    "definition": mapping_def,
    "revision": "1"
}

# Submission
submission_def = file_to_json(here+"/fixtures/submission/form_instance.json")
submission_obj = {
    "revision": 1,
    "mapping_revision": 1,
    "payload": submission_def
}
