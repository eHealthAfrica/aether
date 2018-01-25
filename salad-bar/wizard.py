import json

from library import library_utils
import saladbar.parsers.schemadotorg as parser

lib_name = "schema.org-v3.3"

def pprint(obj):
    print(json.dumps(obj, indent=2))

def main():
    library = library_utils.get_library(lib_name)
    all_props, all_types = parser.load(library)
    

if __name__ == "__main__":
    main()
