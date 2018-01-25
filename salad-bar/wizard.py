import json
import pkgutil

from library import library_utils
import saladbar.parsers as Parsers

SETTINGS = "conf/settings.json"

def pprint(obj):
    print(json.dumps(obj, indent=2))

def load_settings(path):
    with open(path) as f:
        return json.load(f)

def main():
    settings = load_settings(SETTINGS)
    base_type = "%s%s" % (settings.get("$base"), settings.get("basetype_name"))
    for lib_name in settings.get("libraries", {}).keys():
        lib_req = settings.get("libraries", {}).get(lib_name) # requested from this lib
        library = library_utils.get_library(lib_name) # rendered lib
        info = library.get("info")
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
        slim = {
            "http://schema.org/Person":[

                "http://schema.org/address",
                "http://schema.org/birthDate",
                "http://schema.org/birthPlace",
                "http://schema.org/brand",
                "http://schema.org/children",
                "http://schema.org/name"
            ],
            "http://schema.org/Place" : [
                "http://schema.org/address",
                "http://schema.org/geo",
                "http://schema.org/name"
            ],
            "http://schema.org/Thing": [
                "http://schema.org/alternateName",
                "http://schema.org/name"
            ]
        }
        props, types = parser.make_graph(requests, all_props, all_types, depth, slim)
        depends = parser.make_dependency_graph(types, all_types)
        #pprint(depends)
        depends = parser.make_dependency_graph(types, all_types, slim)
        pprint(depends)

if __name__ == "__main__":
    main()
