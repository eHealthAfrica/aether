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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json


from os.path import abspath
from schema_salad import schema, validate, jsonld_context
from schema_salad.ref_resolver import Loader, file_uri


def pprint(obj):
    print(json.dumps(obj, indent=2))

##################################################################################
#             Utility functions to make namespaces Avro Compliant
##################################################################################

def replace_url(test):
    if not isinstance(test, str):
        return test
    flag = "http://"
    if not flag in test:
        return test
    test = test.replace(flag, "")  # cut out http://
    parts = test.split("/")
    if not parts:
        # just namespace
        try:
            parts = test.split(".")
            return ".".join([i for i in parts[::-1]])
        except Exception:
            return test
    namespace = parts[0]
    path = None
    if parts[-1] != namespace:
        path = ".".join(parts[1:])
    # reverse namespace
    parts = namespace.split(".")
    if len(parts) > 1:
        if parts[0] not in ["org", "com", "net", "gov"]:
            namespace = ".".join([i for i in parts[::-1]])
    return ".".join([namespace,path])



#we recurse until the object is just replaced strings or ignored items
def re_namespace(obj):
    if isinstance(obj, str):
        return replace_url(obj)
    if isinstance(obj, list):
        return [re_namespace(i) for i in obj]
    if isinstance(obj, dict):
        return {re_namespace(k): re_namespace(v) for k, v in obj.items()}
    return obj


def check_namespace(fn):
    def wrapper(*args, **kwargs):
        out = fn(*args, **kwargs)
        return re_namespace(out)
    return wrapper


# for some reason the schema salad lib is adding an empty name field to array objects.
# It's useless so we to delete them.
def handle_empty_fields(obj):
    if isinstance(obj, str):
        return
    if isinstance(obj, list):
        return [handle_empty_fields(i) for i in obj]
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            v = obj[k]
            if not v:
                del obj[k]
            else:
                handle_empty_fields(v)


class SaladHandler(object):

    def __init__(self, path, strict=True):
        self.load_salad(path, strict)

    def load_salad(self, path, strict=True):

        metaschema_names, metaschema_doc, metaschema_loader = schema.get_metaschema()
        schema_uri = file_uri(abspath(path))
        schema_raw_doc = metaschema_loader.fetch(schema_uri)

        try:  # parse the schema
            schema_doc, schema_metadata = metaschema_loader.resolve_all(
                schema_raw_doc, schema_uri)
        except (validate.ValidationException) as vale:
            print("Error loading schema %s" % vale)
            raise vale

        # Get the json-ld context and RDFS representation from the schema
        metactx = {}  # type: Dict[str, str]
        if isinstance(schema_raw_doc, dict):
            metactx = schema_raw_doc.get("$namespaces", {})
            if "$base" in schema_raw_doc:
                metactx["@base"] = schema_raw_doc["$base"]
        if schema_doc is not None:
            (schema_ctx, rdfs) = jsonld_context.salad_to_jsonld_context(
                schema_doc, metactx)
        else:
            raise Exception("schema_doc is None??")

        # Create the loader that will be used to load the target document.
        document_loader = Loader(schema_ctx)

        try:

            schema.validate_doc(metaschema_names, schema_doc,
                                metaschema_loader, strict,
                                source=schema_metadata.get("name"))

        except (validate.ValidationException) as vale:
            print("Error validating schema %s" % vale)
            raise vale

        self.schema_doc = schema_doc
        self.document_loader = document_loader
        self.schema_ctx = schema_ctx
        print("Salad schema is valid and loaded")

    def get_avro(self, depends=None):
        avsc_names, avsc_obj = schema.make_avro_schema(
            self.schema_doc, self.document_loader)
        pprint(avsc_obj)
        if not depends:
            return avsc_names, avsc_obj
        avsc_dict = {i.get('name'): i for i in avsc_obj}
        handle_empty_fields(avsc_dict)
        pprint([i for i in avsc_dict.keys()])
        out = {}
        deps = depends.keys()
        for i in avsc_obj:
            name = i.get('name')
            if name in deps:
                reqs = depends.get(name)
                # unpack nested values
                all_props = [i for j in reqs.get(
                    'properties').values() for i in j]
                items = [
                    avsc_dict.get(i) for i in all_props if i in avsc_dict.keys()]
                # split names and namespaces
                prime = avsc_dict.get(name)
                del prime['extends']
                prime['aetherBaseSchema'] = True
                # del avro_item['extends']
                items.append(prime)
                avro_item = []
                for i in items:
                    i = re_namespace(i)
                    parts = i.get('name').split(".")
                    print(parts)
                    i['label'] = parts[-1]
                    i['name'] = ".".join(parts)
                    i['namespace'] = ".".join(parts[:-1])
                    if i.get('aetherBaseSchema') is True:
                        name = i.get('label')
                    avro_item.append(i)


                out[name] = avro_item
        return out
