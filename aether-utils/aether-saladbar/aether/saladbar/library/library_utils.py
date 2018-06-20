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

import os
import csv
import json

HERE = (os.path.dirname(os.path.realpath(__file__)))


class GenericParser(object):

    def __init__(self, headers):
        self._array_columns = []
        self.headers = headers

    def get(self, row):
        obj = {}
        for key in self.headers:
            if key in self._array_columns:
                obj[key] = self.get_array(key, row)
            else:
                obj[key] = self.get_value(key, row)
        return obj.get("id"), obj

    def get_value(self, key, row):
        string_value = row.get(key)
        if string_value and len(string_value) > 0:
            return string_value

    def get_array(self, key, row):
        string_value = row.get(key)
        if string_value and len(string_value) > 0:
            return [i.strip() for i in string_value.split(",")]


class PropertyParser(GenericParser):

    def __init__(self, headers):
        GenericParser.__init__(self, headers)
        self._array_columns = [
            "domainIncludes",
            "rangeIncludes",
            "properties",
            "subproperties",
            "supercedes"
        ]


class TypeParser(GenericParser):

    def __init__(self, headers):
        GenericParser.__init__(self, headers)
        self._array_columns = [
            "domainIncludes",
            "rangeIncludes",
            "properties",
            "subproperties",
            "supercedes",
            "subTypes",
            "subTypeOf"
        ]


def find_libraries():
    libraries = []
    settings_name = 'scrape.json'
    for root, subFolders, files in os.walk(HERE + "/src"):
        if settings_name in files:
            with open("%s/%s" % (root, settings_name)) as f:
                settings = json.load(f)
                settings['path'] = root
                libraries.append(settings)
            if os.path.isfile("%s/%s" % (root, settings.get("output", None))):
                settings['is_built'] = True
            else:
                settings['is_built'] = False
    return libraries


def pprint(obj):
    print(json.dumps(obj, indent=2))


def build_library(lib):
    schema = {}
    base_path = lib.get('path')
    types_file = lib.get('types')
    props_file = lib.get('properties')
    out_file = lib.get('output')
    # Parse Types
    with open("%s/%s" % (base_path, types_file)) as f:
        types = {}
        reader = csv.DictReader(f)
        parser = TypeParser(reader.fieldnames)
        for row in reader:
            _id, line = parser.get(row)
            types[_id] = line
        schema['types'] = types
    # Parse Properties
    with open("%s/%s" % (base_path, props_file)) as f:
        props = {}
        reader = csv.DictReader(f)
        parser = PropertyParser(reader.fieldnames)
        for row in reader:
            _id, line = parser.get(row)
            props[_id] = line
        schema['properties'] = props
    # Write to file
    with open("%s/%s" % (base_path, out_file), "w") as f:
        json.dump(schema, f, indent=2, sort_keys=True)


def get_library(name):
    libs = find_libraries()
    names = [lib.get('name', None) for lib in libs]
    if name not in names:
        raise KeyError(
            "Library named %s not found in available: %s" %
            (name, (names,)))
    lib = [lib for lib in libs if lib.get("name") == name][0]
    if not lib.get("is_built"):
        build_library(lib)
    path = lib.get('path')
    res = lib.get('output')
    data = None
    with open("%s/%s" % (path, res)) as f:
        data = json.load(f)
    return {
        "info": lib,
        "data": data
    }
