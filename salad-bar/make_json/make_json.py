import os
import csv
import json

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
        if string_value and len(string_value) > 0 :
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


def pprint(obj):
    print(json.dumps(obj, indent=2))


def main():
    schema = {}
    here = os.path.dirname(__file__)
    version = "3.3"
    with open("%s/%s/all-layers-types.csv" % (here, version)) as f:
        types = {}
        reader = csv.DictReader(f)
        parser = TypeParser(reader.fieldnames)
        for row in reader:
            _id, line = parser.get(row)
            types[_id] = line

        schema['types'] = types

    with open("%s/%s/all-layers-properties.csv" % (here, version)) as f:
        types = {}
        reader = csv.DictReader(f)
        parser = PropertyParser(reader.fieldnames)
        for row in reader:
            _id, line = parser.get(row)
            types[_id] = line

        schema['properties'] = types

    with open("%s/../all_csv.json" % here, "w") as f:
        json.dump(schema, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
