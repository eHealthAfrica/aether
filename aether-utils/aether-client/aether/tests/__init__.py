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

import json
import os

kernel_url = "http://kernel-test:9000"

kernel_credentials ={
    "username": "admin",
    "password": "adminadmin",
}

odk_credentials ={
    "username": "admin",
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
