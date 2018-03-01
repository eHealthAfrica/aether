import os
import json
import pkgutil

from aether.client import KernelClient

from library import library_utils
import saladbar.parsers as Parsers
from saladbar import salad_handler as salad

SETTINGS = "conf/settings.json"
RES = "wizard_resources"
TMP = "%s/tmp" % RES
SCHEMAS = "schemas/"

def pprint(obj):
    print(json.dumps(obj, indent=2))

def load_settings(path):
    with open(path) as f:
        return json.load(f)

def load_libraries(settings):
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    libraries = {}
    for lib_name in settings.get("libraries", {}).keys():
        lib_req = settings.get("libraries", {}).get(lib_name) # requested from this lib
        library = library_utils.get_library(lib_name) # rendered lib
        info = library.get("info")
        namespaces = info.get("namespaces")
        base = info.get("base")
        parser_name = info.get('parser_type')
        parser = None
        # dynamically import the right parser (filename(-.py) in parsers must match value in scrape.json for the lib)
        for importer, modname, ispkg in pkgutil.iter_modules(Parsers.__path__):
            if modname == parser_name:
                parser = importer.find_module(modname).load_module(modname)
        if not parser:
            raise AttributeError("No valid parser found of type %s" % parser_name)
        all_props, all_types = parser.load(library.get("data"))
        requests = lib_req.get("requirements", None)
        depth = lib_req.get("depth", 0)
        props, types = parser.make_graph(requests, all_props, all_types, depth)
        depends = parser.make_dependency_graph(types, all_types)
        schema_file = lib_req.get("schema_file")
        graph_path = "%s%s" % (SCHEMAS, schema_file)
        graph = parser.write_salad(graph_path, base, namespaces, props, types, base_type)
        libraries[lib_name] = {
            "depends": depends,
            "graph": graph,
            "graph_file": schema_file,
            "namespaces": namespaces
        }
    return libraries


def make_base_salad_doc(imports, namespaces, project=None, base_type=None):
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
    project_file = "%s%s.json" % (SCHEMAS, project)
    with open(project_file, "w") as f:
        json.dump(doc, f, indent=2)

def file_to_json(path):
    with open(path) as f:
        return json.load(f)

def register_project(client, name):
    path = "%s/%s.json" % (SCHEMAS, name)
    project_def = file_to_json(path)
    obj = {
        "revision": "1",
        "name": name,
        "salad_schema": project_def,
        "jsonld_context": "[]",
        "rdf_definition": "[]"
    }
    client.Resource.Project.add(obj)

def register_schemas(client, project):
    loc = SCHEMAS+ "/%s"
    files = os.listdir(SCHEMAS)
    names = []
    for f in files:
        try:
            if f.split(".")[1] == "avsc":
                names.append([f.split(".")[0], f])
        except Exception as e:
            print("Error parsing %s" % f)
    for name, fname in names:
        path = "%s/%s" % (SCHEMAS, fname)
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
            "name": "My"+name,
            "masked_fields": "[]",
            "transport_rule": "[]",
            "mandatory_fields": "[]",
            "schema": schema.id,
            "project": project_id

        }
        client.Resource.ProjectSchema.add(project_schema_obj)



def main():
    settings = load_settings(SETTINGS)
    libraries = load_libraries(settings)
    imports = []
    namespaces = {}
    for lib in libraries.values():
        rel_path = "./%s" % lib.get('graph_file')
        imports.append(rel_path)
        for k,v in lib.get('namespaces', {}).items():
            namespaces[k] = v
    all_depends = {k : v for key, lib in libraries.items() for k,v in lib.get('depends', {}).items()}
    project = settings.get("project")
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    make_base_salad_doc(imports, namespaces, project, base_type)
    project_file = "%s%s.json" % (SCHEMAS, project)
    salad_handler = salad.SaladHandler(project_file)
    avsc_dict = salad_handler.get_avro(all_depends)
    for k,v in avsc_dict.items():
        filename = "%s%s.avsc" % (SCHEMAS, k.split(".org/")[1])  # Fix this .org nonsense...
        with open(filename, "w") as f:
            json.dump(v, f, indent=2)
    kernel_url = settings.get("kernel_url")
    kernel_user = settings.get("kernel_user")
    kernel_pw = settings.get("kernel_pw")
    kernel_credentials = {"username": kernel_user, "password": kernel_pw}
    client = KernelClient(url= kernel_url, **kernel_credentials)
    register_project(client, project)
    register_schemas(client, project)


if __name__ == "__main__":
    main()
