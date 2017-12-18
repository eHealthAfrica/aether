from aether.client import KernelClient, ODKModuleClient
import json
import os

def file_to_json(path):
    with open(path) as f:
        return json.load(f)

def pprint(obj):
    print(json.dumps(obj, indent=2))


kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

odk_credentials ={
    "username": "admin-odk",
    "password": "adminadmin",
}

kernel = KernelClient(url= "http://kernel.aether.local:8000", **kernel_credentials)
resource = kernel.Resource

#Register Project
project_name = "DecemberDemo"
project_def = file_to_json("./project/salad/salad.json")
project_obj = {
    "revision": "1",
    "name": project_name,
    "salad_schema": json.dumps(project_def),
    "jsonld_context": "[]",
    "rdf_definition": "[]"
}

resource.Project.add(project_obj)
kernel.refresh()
resource = kernel.Resource
project_id = resource.Project.DecemberDemo.id

#Register Schema
schema_dir ="./project/schemas"
schema_files = os.listdir(schema_dir)
for filename in schema_files:
    name = filename.split(".")[0]
    definition = file_to_json("%s/%s" % (schema_dir, filename))
    schema_obj = {
        "name": name,
        "type": "record",
        "revision": "1",
        "definition": json.dumps(definition)
    }
    resource.Schema.add(schema_obj)

kernel.refresh()
resource = kernel.Resource
schema_names = [fn.split(".")[0] for fn in schema_files]

#Register ProjectSchema
for name in schema_names:
    schema_id = resource.Schema.get(name).id
    project_schema_obj = {
        "revision": "1",
        "schema":schema_id,
        "name": name,
        "project": project_id,
        "masked_fields": "[]",
        "transport_rule": "[]",
        "mandatory_fields": "[]"
    }
    resource.ProjectSchema.add(project_schema_obj)

#Register Mapping
kernel.refresh()
resource = kernel.Resource
project_schema_ids = {
    name : resource.ProjectSchema.get(name).id
    for name in schema_names
}
mapping_def = file_to_json("./project/mappings/form-mapping.json")
mapping_def["entities"] = project_schema_ids
mapping_obj = {
    "name": "microcensus",
    "definition": json.dumps(mapping_def),
    "revision": "1",
    "project": project_id
}
resource.Mapping.add(mapping_obj)

#Register Surveyor
odk = ODKModuleClient(url= "http://odk.aether.local:8443", **odk_credentials)
username = "dave"
surveyor_obj = {
    "username": username,
    "password": "adminadmin"
}
odk.Resource.Surveyor.add(surveyor_obj)
odk.refresh()
user = odk.Resource.Surveyor.search({"username": username})[0]

#Register Survey
kernel.refresh()
resource = kernel.Resource
mapping_id = resource.Mapping.microcensus.id
survey_obj = {
    "mapping_id": mapping_id,
    "surveyors": [user.id],
    "name": "microcensus"
}
odk.Resource.Survey.add(survey_obj)
odk.refresh()
survey = odk.Resource.Survey.search({"mapping_id": mapping_id})[0]

#Register XForm
xml_data = None
with open("./project/xform/form1.xml") as f:
    xml_data = f.read()
xform_obj = {
    "surveyors": [user.id],
    "xml_file": None,
    "xml_data": xml_data,
    "description": "microcensus survey",
    "created_at": None,
    "survey": survey.mapping_id
}
odk.Resource.XForm.add(xform_obj)
print ("Setup Complete")
