#!/usr/bin/env python2

import os
import json
import pkgutil
import sys

from aether.client import KernelClient

import aether.saladbar.library.library_utils as library_utils
# from library import library_utils
import aether.saladbar.saladbar.parsers as Parsers
# from saladbar import parsers as Parsers
# from saladbar import salad_handler as salad
import aether.saladbar.saladbar.salad_handler as salad

HERE = (os.path.dirname(os.path.realpath(__file__)))
SETTINGS = "%s/conf/settings.json" % HERE
TEST_SETTINGS = "%s/conf/test_settings.json" % HERE
RES = "%s/wizard_resources" % HERE
TMP = "%s/tmp" % RES
SCHEMAS = "%s/schemas/" % HERE
TEST_SCHEMAS = "%s/test-schemas/" % HERE

# alais raw_input for python3
if sys.version_info >= (3, 0):
    def raw_input(prompt):
        return input(prompt)

def pprint(obj):
    print(json.dumps(obj, indent=2))


def load_settings(path):
    with open(path) as f:
        return json.load(f)


def load_libraries(settings, schema_path=SCHEMAS):
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    libraries = {}
    for lib_name in settings.get("libraries", {}).keys():
        lib_req = settings.get("libraries", {}).get(
            lib_name)  # requested from this lib
        library = library_utils.get_library(lib_name)  # rendered lib
        info = library.get("info")
        namespaces = info.get("namespaces")
        base = info.get("base")
        parser_name = info.get('parser_type')
        parser = None
        # dynamically import the right parser (filename(-.py) in parsers must
        # match value in scrape.json for the lib)
        for importer, modname, ispkg in pkgutil.iter_modules(Parsers.__path__):
            if modname == parser_name:
                parser = importer.find_module(modname).load_module(modname)
        if not parser:
            raise AttributeError(
                "No valid parser found of type %s" %
                parser_name)
        all_props, all_types = parser.load(library.get("data"))
        requests = lib_req.get("requirements", None)
        depth = lib_req.get("depth", 0)
        props, types = parser.make_graph(requests, all_props, all_types, depth)
        depends = parser.make_dependency_graph(types, all_types)
        schema_file = lib_req.get("schema_file")
        graph_path = "%s%s" % (schema_path, schema_file)
        graph = parser.write_salad(
            graph_path,
            base,
            namespaces,
            props,
            types,
            base_type)
        libraries[lib_name] = {
            "depends": depends,
            "graph": graph,
            "graph_file": schema_file,
            "namespaces": namespaces
        }
    return libraries

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


def make_base_salad_doc(imports, namespaces, project=None, base_type=None, schema_path=SCHEMAS):
    doc = None
    with open("%s/base_salad.json" % RES) as f:
        doc = json.load(f)
    doc["$base"] = "http://demo.eha.org"
    doc["$namespaces"] = namespaces
    base_doc = None
    with open("%s/base_model.json" % RES) as f:
        base_doc = json.load(f)
    base_doc['name'] = base_type
    graph = [{"$import": i} for i in imports]
    graph.append(base_doc)
    doc['$graph'] = graph
    project_file = "%s%s.json" % (schema_path, project)
    with open(project_file, "w") as f:
        json.dump(doc, f, indent=2)


def prompt_schema_clean(prompt, question, schema_path=SCHEMAS):
    contents = os.listdir(schema_path)
    if not contents:
        return
    print(prompt)
    pprint(contents)
    if ask(question):
        clean_schemas_folder()


def clean_schemas_folder(schema_path=SCHEMAS):
    contents = os.listdir(schema_path)
    if not contents:
        return
    for f in contents:
        path = "%s/%s" % (schema_path, f)
        os.remove(path)


def file_to_json(path):
    with open(path) as f:
        return json.load(f)


def register_project(client, name, schema_path=SCHEMAS):
    path = "%s/%s.json" % (schema_path, name)
    project_def = file_to_json(path)
    obj = {
        "revision": "1",
        "name": name,
        "salad_schema": project_def,
        "jsonld_context": "[]",
        "rdf_definition": "[]"
    }
    client.Resource.Project.add(obj)


def register_schemas(client, project, schema_path=SCHEMAS):
    loc = SCHEMAS + "/%s"
    files = os.listdir(schema_path)
    names = []
    for f in files:
        try:
            if f.split(".")[1] == "avsc":
                names.append([f.split(".")[0], f])
        except Exception as e:
            print("Error parsing %s" % f)
    for name, fname in names:
        path = "%s/%s" % (schema_path, fname)
        definition = file_to_json(path)
        schema_obj = {
            "name": name,
            "type": "record",
            "revision": "1",
            "definition": definition
        }
        client.Resource.Schema.add(schema_obj)
    project_id = client.Resource.Project.get(project).id
    for schema in client.Resource.Schema:
        name = schema.name
        project_schema_obj = {
            "revision": "1",
            "name": name,
            "masked_fields": "[]",
            "transport_rule": "[]",
            "mandatory_fields": "[]",
            "schema": schema.id,
            "project": project_id

        }
        client.Resource.ProjectSchema.add(project_schema_obj)


def ask(question):
    while True:
        reply = str(raw_input(question + ' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False

def test_setup():
    try:
        os.mkdir(TEST_SCHEMAS)
    except OSError as err:
        pass
    settings = load_settings(TEST_SETTINGS)
    libraries = load_libraries(settings, schema_path=TEST_SCHEMAS)
    imports = []
    namespaces = {}
    for lib in libraries.values():
        rel_path = "./%s" % lib.get('graph_file')
        imports.append(rel_path)
        for k, v in lib.get('namespaces', {}).items():
            namespaces[k] = v
    all_depends = {k: v for key, lib in libraries.items()
                   for k, v in lib.get('depends', {}).items()}
    project = settings.get("project")
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    make_base_salad_doc(imports, namespaces, project, base_type, schema_path=TEST_SCHEMAS)
    project_file = "%s%s.json" % (TEST_SCHEMAS, project)
    salad_handler = salad.SaladHandler(project_file)
    avsc_dict = salad_handler.get_avro(all_depends)
    avsc_dict = re_namespace(avsc_dict)
    for k, v in avsc_dict.items():
        filename = "%s%s.avsc" % (TEST_SCHEMAS, k.split(".")[-1])
        with open(filename, "w") as f:
            json.dump(v, f, indent=2)
    kernel_url = settings.get("kernel_url")
    kernel_user = settings.get("kernel_user")
    kernel_pw = settings.get("kernel_pw")
    kernel_credentials = {"username": kernel_user, "password": kernel_pw}
    client = KernelClient(url=kernel_url, **kernel_credentials)
    register_project(client, project, schema_path=TEST_SCHEMAS)
    register_schemas(client, project, schema_path=TEST_SCHEMAS)
    clean_schemas_folder(schema_path=TEST_SCHEMAS)

def main():
    prompt_schema_clean(
        "These files already exist in the schemas folder",
        "Delete existing schemas before building library?"
    )
    settings = load_settings(SETTINGS)
    libraries = load_libraries(settings)
    imports = []
    namespaces = {}
    for lib in libraries.values():
        rel_path = "./%s" % lib.get('graph_file')
        imports.append(rel_path)
        for k, v in lib.get('namespaces', {}).items():
            namespaces[k] = v
    all_depends = {k: v for key, lib in libraries.items()
                   for k, v in lib.get('depends', {}).items()}
    project = settings.get("project")
    ok = ask("Continue with setup of project titled: %s" % (project))
    if not ok:
        return
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    make_base_salad_doc(imports, namespaces, project, base_type)
    project_file = "%s%s.json" % (SCHEMAS, project)
    salad_handler = salad.SaladHandler(project_file)
    avsc_dict = salad_handler.get_avro(all_depends)
    avsc_dict = re_namespace(avsc_dict)
    for k, v in avsc_dict.items():
        # Fix this .org nonsense...
        filename = "%s%s.avsc" % (SCHEMAS, k.split(".")[-1])
        with open(filename, "w") as f:
            json.dump(v, f, indent=2)
    kernel_url = settings.get("kernel_url")
    kernel_user = settings.get("kernel_user")
    kernel_pw = settings.get("kernel_pw")
    kernel_credentials = {"username": kernel_user, "password": kernel_pw}
    client = KernelClient(url=kernel_url, **kernel_credentials)
    ok = ask(
        "Setup of project titled: %s complete. Register generated schemas with Aether?" %
        (project))
    if ok:
        register_project(client, project)
        register_schemas(client, project)
        prompt_schema_clean(
            "Setup Complete.",
            "Delete local copy of generated schemas?"
        )
    else:
        prompt_schema_clean(
            "Artifacts generated but not registered.",
            "Delete schema artifacts?"
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_setup()
        else:
            print("Invalid argument: %s" % sys.argv[1])
    else:
        main()
