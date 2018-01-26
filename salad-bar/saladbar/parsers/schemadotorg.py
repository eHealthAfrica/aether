import re
import os
import copy
import json
from collections import OrderedDict

DOM = ".org/" # TODO we need a way to handle multiple domains


class Property(object):
    _flat_types = {
        'http://schema.org/Boolean': {'type': ['boolean?']},
        'http://schema.org/Date': {
            'type': [
                "string?",
                'string[]?'
            ]
        },
        'http://schema.org/DateTime': {
            'type': [
                "string?",
                'string[]?'
            ]
        },
        'http://schema.org/Float': {
            'type': [
                'float?',
                'float[]?'
                ]
            },
        'http://schema.org/Integer': {
            'type': [
                'int?',
                'int[]?'
            ]
        },
        'http://schema.org/Number': {
            'type': [
                'int?',
                'int[]?'
            ]
        },
        'http://schema.org/Text': {
            'type': [
                'string?',
                'string[]?'
            ]
        },
        'http://schema.org/Time': {
            'type': [
                'string?',
                'string[]?'
            ]
        },
        'http://schema.org/URL': {
            'type': [
                'string?',
                'string[]?'
            ]
        }
    }
    def __init__(self, obj, simplify=True):
        self.json = obj
        self.name = obj['id']
        self.label = obj['label']
        self.doc = obj['comment']
        self.relationships = {}
        self.records = OrderedDict()
        self.salad_definition = self.get_salad_from_property_def(**obj)
        self.get_relationships()
        self.simple = None if simplify else False
        self.simple = self.is_simple()

    def is_simple(self):
        #whether or not this property can be reduced into simple avro types
        if self.simple is not None:
            return self.simple
        if len(self.records) == 0: #has no records, should not be included
            self.simple = True
            return self.simple
        try:
            self.get_simplified_types()
        except TypeError as e:
            self.simple = False
            return False

        self.simple = True
        return self.simple

    def get_relationships(self):
        if self.json.get("subproperties"):
            self.relationships['children'] = self.json.get("subproperties")
        if self.json.get("subPropertyOf"):
            self.relationships['parents'] = self.json.get("subproperties")



    def get_simplified_types(self):
        #returns the flattened structure for use by a parent property
        defs = []
        for type_name in self.json.get("rangeIncludes"):
            try:
                definition = Property._flat_types.get(type_name, None).get('type')
            except AttributeError as e:
                raise TypeError("No type matching %s" % type_name)
            defs.extend(definition)
        defs = set(defs)
        if len(defs) > 2:
            raise TypeError
        label = self.name.split(DOM)[1]
        return {
            "name": self.label,
            "doc": self.doc,
            "jsonldPredicate": "%s" % (self.name),
            "type": list(defs)
        }

    def get_salad_from_property_def(self, **obj):
        record = {
            "name": self.name,
            "type": "record"
        }
        if obj.get("comment_plain"):
            record["doc"] = obj.get("comment_plain")
        if obj.get("rangeIncludes"):
            fields = self.build_ranges(obj["id"], obj.get("rangeIncludes"))
        try:
            record["fields"] = fields
        except Exception as e:
            pass
            #no fields, likely deprecated
        return record

    def build_ranges(self, super_type, range_obj):
        fields = []
        for type_name in range_obj:
            if not self.records.get(type_name):
                self.records[type_name] = None # create a stub for the record type to fill later
            predicate_id = "%s" % (type_name)
            #these nested record requirements are annoying should just be type_name but it creates a predicate collision
            label = type_name.split(DOM)[1]
            name = "%s-id" % (label)
            body = {
                "name": name,
                "type": ["string?","string[]?"],
                "jsonldPredicate" : {
                    "_type": "@id",
                    "_id" : predicate_id
                }
            }
            simple_type = simple_types(type_name)
            if simple_type:
                body["name"] = type_name.split(DOM)[1]
                body["type"] = simple_type
                body ["jsonldPredicate"] = "%s:%s" % ("xsd", simple_type[0][:-1])
            elif self.records.get(type_name):
                #TODO check if record is simple
                pass
            fields.append(body)
        return fields

    def add_records(self, records):
        for k in self.records.keys():
            self.records[k] = records.get(k, None)

    def get_reference(self):
        #returns full reference to this Property (if it requires one and is NOT simple)
        return {
            "name": self.label,
            "jsonldPredicate": "%s" % (self.name),
            "type": [
                "null",
                "%s" % (self.name)
            ]
        }

    def get_salad_definition(self):
        #returns Salad definition for this field or NONE if it's simple
        return self.salad_definition


class Record(object):

    def __init__(self, all_properties, obj, simplify=True):
        self.all_properties = all_properties
        self.json = obj
        self.fields = []
        self.topics = []
        self.relationships = {}
        self.salad_definition = self.get_record_from_type(**obj)
        self.get_relationships()
        self.simple = None if simplify else False

    def add_extension(self, extension):
        record_salad = self.salad_definition
        parent = record_salad.get('extends')
        if not parent:
            record_salad['extends'] = extension
        elif isinstance(parent, list) and isinstance(extension, list):
            record_salad['extends'] = extension + parent
        else:
            extends = []
            for item in [parent, extension]:
                if isinstance(item, list):
                    extends.extend(item)
                else:
                    extends.append(item)
            record_salad['extends'] = extends
        self.salad_definition = record_salad


    def is_simple(self):
        if self.simple != None:
            return self.simple
        self.simple = False
        if self.name in Property._flat_types.keys():
            self.simple = True
        if len(self.topics) <= 0:
            self.simple = True
        return self.simple

    def get_relationships(self):
        if self.json.get("subTypes"):
            self.relationships['children'] = self.json.get("subTypes")
        if self.json.get("subTypeOf"):
            self.relationships['parents'] = self.json.get("subTypeOf")

    def get_record_from_type(self, **obj):
        self.name = obj["id"]
        record = {
            "name": self.name,
            "type": "record"
        }
        if obj.get("comment_plain"):
            record["doc"] = obj.get("comment")
        field_topics = obj.get("properties", []) # this never returns []
        field_topics = field_topics if field_topics else [] # no idea why this works instead
        specific_properties = obj.get("specific_properties", [])
        try:
            field_topics = list(set(field_topics + specific_properties))
        except Exception as e:
            raise TypeError
        if len(field_topics) > 0:
            for topic in field_topics:
                self.topics.append(topic)
                prop = self.all_properties.get(topic)
                if not prop:
                    print("%s has no properties..." % topic)
                else:
                    if prop.is_simple():
                        self.fields.append(prop.get_simplified_types())
                    else:
                        self.fields.append(prop.get_reference())

        record['fields'] = self.fields
        return record

def get_salad(graph, namespaces, base):
    body = {
        "$base": base,
        "$namespaces" : namespaces,
        "$graph":graph
    }
    return body


def pprint(obj):
    print(json.dumps(obj, indent=2))


def simple_types(name=None):
    types = Property._flat_types
    if name:
        return types.get(name, {}).get('type')
    else:
        return types

def load(obj):
    properties = OrderedDict()
    records = OrderedDict()
    for name, property in obj['properties'].items():
        prop = Property(property)
        properties[prop.name] = prop

    for name, type in obj['types'].items():
        record = Record(properties, type)
        records[record.name] = record

    return properties, records

def load_file(path):
    with open(path) as f:
        spec = json.load(f)
        return load(spec)

def get_salad_graph(properties, records, document_model=None):
    graph = []
    for key in properties.keys():
        prop = properties[key]
        if not prop.is_simple():
            prop_salad = prop.get_salad_definition()
            graph.append(prop_salad)

    for key in records.keys():
        record = records[key]
        if not record.is_simple():
            if document_model:
                #inherit from document model
                record.add_extension(document_model)
            graph.append(record.salad_definition)
    return graph

def write_salad(path, base, namespaces, properties, records, document_model=None):
    graph = get_salad_graph(properties, records, document_model)
    output = get_salad(graph, namespaces, base)
    write_json(path, output)

def resolve_property_graph(name, records, properties, depth, max_depth, captured, selected_fields=None):
    if depth > max_depth:
        return captured
    current_depth = depth +1
    if not name in properties.keys():
        return captured
    prop = properties[name]
    for i in sorted(prop.records.keys()):
        if not i in captured.get("records"):
            captured["records"].append(i)
            captured = resolve_record_graph(i, records, properties, current_depth, max_depth, captured, selected_fields)

    return captured

def resolve_record_graph(name, records, properties, depth, max_depth, captured, selected_fields=None):
    current_depth = depth
    if not name in records.keys():
        return captured
    record = records[name]
    for i in sorted(record.topics):
        if selected_fields and  i not in selected_fields.get(name, []):
            continue
        if not i in captured.get("properties"):
            captured['properties'].append(i)
            captured = resolve_property_graph(i, records, properties, current_depth, max_depth, captured, selected_fields)

    return captured

def make_graph(requirements, properties, records, max_property_depth=3, selected_fields=None):
    captured = {
        "records": [],
        "properties" : []
    }
    for name in sorted(requirements):
        captured = resolve_record_graph(name, records, properties, 0, max_property_depth, captured, selected_fields)

    properties = {name: properties[name] for name in captured["properties"]}
    records = {name: records[name] for name in captured["records"]}
    print ("returning\n\t #%s records\n\t #%s properties\nfor requirements\n%s\n\t@ depth %s" % (
            len(records.keys()),
            len(properties),
            json.dumps(requirements, indent=2),
            max_property_depth
        ))
    return properties, records

def make_dependency_graph(graphed_records, records, limited_properties={}):
    graph = {}
    for key in graphed_records:
        record = records[key]
        if record.is_simple():
            continue # ignore
        parents = record.relationships.get("parents")
        children = record.relationships.get("children")
        graph[record.name] = {}
        permitted = set([i for val in limited_properties.values() for i in val])
        if permitted:
            all_properties = [i for i in sorted(record.topics) if i in permitted]
        else:
            all_properties = [i for i in sorted(record.topics)]
        if parents:
            lineage = get_lineage(key, "parents", records)
            graph[record.name]['parents'] = lineage
            parental_properties = get_parental_properties(all_properties, lineage, records, limited_properties)
            graph[record.name]['properties'] = parental_properties
        else:
            graph[record.name]['properties'] = all_properties

    return graph

def get_parental_properties(properties, lineage, all_records, limited_properties={}):
    output = {}
    permitted = set([i for val in limited_properties.values() for i in val])
    props = set(properties)
    for x, parent in enumerate(flatten(lineage[::-1])):
        if output.get(parent):
            continue #already got this one...
        parental_fields = sorted(all_records.get(parent).topics)
        if permitted:
            unique_fields = sorted([i for i in props if i in parental_fields if i in permitted])
        else:  # All properties are allowed
            unique_fields = sorted([i for i in props if i in parental_fields])
        output[parent] = unique_fields
        props = props.difference(unique_fields)
    return output



def flatten(heirarchy):
    for item in heirarchy:
        if isinstance(item, list):
            for i in flatten(item[::-1]):
                yield i
        else:
            yield item


def get_lineage(name, direction, records):
    record = records.get(name)
    if not record:
        return []
    rels = record.relationships.get(direction)
    output = []
    if rels:
        if len(rels) > 1:
            output = [get_lineage(rel, direction, records) for rel in rels if get_lineage(rel, direction, records)]
        elif len(rels) == 1:
            output = get_lineage(rels[0], direction, records)
        else:
            output = None
    else:
        return [record.name]
    return [record.name] + output




def write_json(path, obj):
    with open(path, "w") as f2:
            json.dump(obj, f2, indent=2)


def test_graph():
    all_properties, all_records = load("all_csv.json")
    request = [
        "http://schema.org/Patient"
    ]
    #a subset of records and properties base on the requested entities
    properties, records = make_graph(request, all_properties, all_records, 0)
    write_salad('limited.json', properties, records, document_model="http://ehealthafrica.org/BaseModel")

    dependency_graph = make_dependency_graph(records, all_records)
    #pprint(dependency_graph)
    write_json("depends.json", dependency_graph)




if __name__ == "__main__":
    test_graph()
