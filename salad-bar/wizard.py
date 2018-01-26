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
        print("name: " +k)
        pprint(all_depends.get(k))
        pprint(v)











if __name__ == "__main__":
    main()
