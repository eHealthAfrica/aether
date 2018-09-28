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


def file_to_json(path):
    with open(path) as f:
        return json.load(f)


here = os.path.dirname(os.path.realpath(__file__))

# Projects
project_name = "TestProject"
project_template = {
    "revision": "1",
    "name": None
}

# Schemas

schema_file = here + "/schema/schemas.avro"
schema_definitions = file_to_json("%s" % (schema_file))

schema_template = {
    "name": None,
    "type": "record",
    "revision": "1",
    "definition": None
}

# Project Schemas

project_schema_template = {
    "revision": "1",
    "name": None
}

# Mapping

mapping_name = 'VaccineReport'
mapping_template = {
    "name": mapping_name,
    "definition": None,
    "revision": "1"
}

mapping_file = here + "/mappings/mapping.json"
mapping_definition = file_to_json("%s" % (mapping_file))

# Submission

submission_template = {
    "revision": 1,
    "mapping_revision": 1,
    "payload": None
}


def get_submission_payloads():
    submission_file = here + "/submission/submissions_1000.json"
    return file_to_json("%s" % (submission_file))
