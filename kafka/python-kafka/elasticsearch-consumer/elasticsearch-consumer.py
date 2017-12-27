import ast
import os
import json
import sys
import avro.schema

from aether.client import KernelClient
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

#Default Kernel Credentials
kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

try:
    kernel = KernelClient(url= "http://kernel.aether.local:8000", **kernel_credentials)
except Exception as ke:
    #TODO find proper Exception type
    kernel = None
    print ("Error initializing connection to Aether: %s" % ke)
    sys.exit(1) # Kill consumer with error


try:
    es = Elasticsearch(sniff_on_start=True) #default connection on localhost
    print (es.info())
except TransportError as ese:
    print("Could not connect to Elasticsearch Instance")
    sys.exit(1) # Kill consumer with error

def pprint(obj):
    print(json.dumps(obj, indent=2))


class ESConsumerManager(object):

    def __init__(self):
        self.consumer_groups = {} # index_name : consumer group
        self.load_indices()


    def load_indices(self):
        index_path = "%s/index" % FILE_PATH
        if os.path.isdir(index_path):
            index_files = os.listdir(index_path)
            for index_file in index_files:
                self.register_index(index_path, index_file)

    def register_index(self, index_path, index_file):
        index_name = index_file.split(".")[0]
        data = None
        path = "%s/%s" % (index_path, index_file)
        with open(path) as f:
            data = json.load(f)
        if es.indices.exists(index=index_name):
            print ("index %s already exists, skipping" % index_name)
        else:
            print ("Creating Index %s" % index_name)
            es.indices.create(index=index_name, body=data)
        self.start_consumer_group(index_name, data)


    def start_consumer_group(self, index_name, index_body):
        self.consumer_groups[index_name] = ESConsumerGroup(index_name, index_body)

class ESConsumerGroup(object):

    def __init__(self, index_name, index_body):
        self.name = index_name
        self.processors = {}
        self.intuit_sources(index_body)

    def intuit_sources(self, index_body):
        for name, instr in index_body.get("mappings", {}).items():
            self.processors[name] = ESItemProcessor(name, instr)

class ESItemProcessor(object):

    def __init__(self, type_name, type_instructions):
        self.pipeline = []
        self.schema = None
        self.schema_obj = None
        self.type = type_name
        self.get_avro()
        self.load(type_instructions)

    def deserialize(self, doc):
        return doc

    def get_avro(self):
        schemas = kernel.Resource.Schema
        for schema in schemas:
            if schema.name.lower() == self.type:
                print ("%s matches %s" % (schema.name, self.type))
                try:
                    definition = ast.literal_eval(str(schema.definition))
                    self.schema_obj = definition
                    self.schema = avro.schema.Parse(json.dumps(definition))
                except Exception as ave:
                    print ("Error parsing Avro schema for type %s" % self.type)
                    raise ave
        if not self.schema:
            raise TypeError("No registered schema in Aether looks like indexed type: %s" % self.type)

    def load(self, type_instructions):
        for key, value in type_instructions.items():
            if key in ["_parent", "_child"]:
                res = {"function": "_add%s" % key}
                res.update(self._find_matching_predicate(value))
                self.pipeline.append(res)
            elif key == "properties":
                if "location" in value.keys():
                    res = {"function": "_add_geopoint"}
                    res.update(self._find_geopoints(value))
                    self.pipeline.append(res)
        pprint(self.pipeline)

    def process(self, doc):
        doc = self.deserialize(doc)
        for instr in self.pipeline:
            doc = self.exec(doc, instr)
        pass

    def exec(self, doc, instr):
        fn = getattr(self, instr.get("function"))
        return fn(doc, instr)

    def _add_parent(self, doc, **kwargs):
        #field_name
        doc['_parent'] = "fake"
        pass

    def _add_child(self, doc, **kwargs):
        doc['_child'] = "fake"
        pass

    def _add_geopoint(self, doc, **kwargs):
        #field_name, lat, lon
        pass

    def _find_matching_predicate(self, obj):
        #looks for membership of lowercase name in one of the fields in the schema
        name = obj.get("type")
        for field in self.schema_obj.get("fields"):
            test = field.get("name", "").lower()
            if name.lower() in test:
                if "jsonldPredicate" in field.keys():
                    #matches and is an ID, good enough for us!
                    return {"field_name": field.get("name")}
        raise ValueError("No matching field found for name %s in type " % (name, self.type))

    def _find_geopoints(self, obj):
        res = {"field_name": "location"}
        for field in self.schema_obj.get("fields"):
            test = field.get("name", "").lower()
            if test in ["lat", "latitude"]:
                res["lat"] = field.get("name")
            elif test in ["lon", "lng", "long", "longitude"]:
                res["lon"] = field.get("name")
        if not "lat" and "lon" in res:
            raise ValueError("Couldn't resolve geopoints for field %s of type %s" % ("location", self.type))
        return res


if __name__ == "__main__":
    manager = ESConsumerManager()
