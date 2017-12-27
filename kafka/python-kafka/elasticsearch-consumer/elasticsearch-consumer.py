import ast
import os
import io
import json
import sys
import threading
import avro.schema
import avro.io

from time import sleep as Sleep
from aether.client import KernelClient
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from kafka import KafkaConsumer

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

#Default Kafka Port
KAFKA_HOST = "localhost:29092"

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
            print ("index %s already exists, skipping creation." % index_name)
        else:
            print ("Creating Index %s" % index_name)
            es.indices.create(index=index_name, body=data)
        self.start_consumer_group(index_name, data)


    def start_consumer_group(self, index_name, index_body):
        self.consumer_groups[index_name] = ESConsumerGroup(index_name, index_body)

    def stop_group(self, index_name):
        self.consumer_groups[index_name].stop()

    def stop(self):
        for key in self.consumer_groups.keys():
            self.stop_group(key)

class ESConsumerGroup(object):
    # Group of consumers (1 per topic) pushing to an ES index

    def __init__(self, index_name, index_body):
        self.name = index_name
        self.consumers = {}
        self.intuit_sources(index_body)

    def intuit_sources(self, index_body):
        for name, instr in index_body.get("mappings", {}).items():
            processor = ESItemProcessor(name, instr)
            self.consumers[processor.topic_name] = ESConsumer(self.name, processor)
            self.consumers[processor.topic_name].start()

    def stop(self):
        for name in self.consumers.keys():
            self.consumers[name].stop()

class ESConsumer(threading.Thread):
    # A single consumer subscribed to topic, pushing to an index
    # Runs as a daemon to avoid weird stops
    def __init__(self, index, processor):
        self.processor = processor
        self.index = index
        self.es_type = processor.es_type
        self.topic = processor.topic_name
        self.consumer_timeout = 10
        self.group_name = "elastic_%s_%s" % (self.index, self.es_type)
        self.sleep_time = 10
        print(self.group_name)
        self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_HOST,
                                 group_id=self.group_name,
                                 auto_offset_reset='earliest',
                                 consumer_timeout_ms=1000)
        '''
        self.consumer = KafkaConsumer(
                            group_id=self.group_name,
                            auto_offset_reset='earliest',
                            bootstrap_servers=[KAFKA_HOST]) #TODO kill auto_offset
        '''
        self.stopped = False
        super(ESConsumer, self).__init__()

    def run(self):
        self.consumer.subscribe([self.topic])
        total_wait = 0
        while True:
            last_offset = None
            raw_rows = self.consumerReady()
            if raw_rows:
                total_wait = 0
                for parition, messages in raw_rows.items():
                    for row in messages:
                        doc = self.processor.process(row)
                        last_offset = row.offset
                if last_offset:
                    print("index: %s -> %s offset: %s" % (self.index, self.topic, last_offset))
            else:
                total_wait += self.consumer_timeout
                print("consumer group %s not ready, waiting %s seconds." % (self.group_name, self.consumer_timeout))
                print("waited %s seconds so far..." % total_wait)
            if self.stopped:
                break
            else:
                Sleep(self.sleep_time)

        print ("Shutting down consumer %s | %s" % (self.index, self.topic))
        self.consumer.close()
        return

    def consumerReady(self):
        res = self.consumer.poll(self.consumer_timeout)
        return res

    def stop(self):
        print ("%s caught stop signal" % (self.group_name))
        self.stopped = True

class ESItemProcessor(object):

    def __init__(self, type_name, type_instructions):
        self.pipeline = []
        self.schema = None
        self.schema_obj = None
        self.es_type = type_name
        self.topic_name = None
        self.get_avro()
        self.load(type_instructions)

    def deserialize(self, doc):
        bytes_reader = io.BytesIO(doc.value)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)
        doc = reader.read(decoder)
        return doc

    def get_avro(self):
        schemas = kernel.Resource.Schema
        for schema in schemas:
            if schema.name.lower() == self.es_type:
                print ("%s matches %s" % (schema.name, self.es_type))
                self.topic_name = schema.name
                try:
                    definition = ast.literal_eval(str(schema.definition))
                    self.schema_obj = definition
                    self.schema = avro.schema.Parse(json.dumps(definition))
                except Exception as ave:
                    print ("Error parsing Avro schema for type %s" % self.es_type)
                    raise ave
        if not self.schema:
            raise TypeError("No registered schema in Aether looks like indexed type: %s" % self.es_type)

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
        return doc

    def exec(self, doc, instr):
        fn = getattr(self, instr.get("function"))
        return fn(doc, **instr)

    def _add_parent(self, doc, field_name=None, **kwargs):
        try:
            doc["_parent"] = self._get_doc_field(doc, field_name)
        except Exception as e:
            print ("Could not add parent to doc type %s. Error: %s" % (self.es_type, e))
        return doc

    def _add_child(self, doc, field_name=None, **kwargs):
        try:
            doc["_child"] = self._get_doc_field(doc, field_name)
        except Exception as e:
            print ("Could not add parent to doc type %s. Error: %s" % (self.es_type, e))
        return doc

    def _add_geopoint(self, doc, field_name=None, lat=None, lon=None, **kwargs):
        geo = {}
        try:
            geo["lat"] = self._get_doc_field(doc, lat)
            geo["lon"] = self._get_doc_field(doc, lon)
            doc[field_name] = geo
        except Exception as e:
            print ("Could not add parent to doc type %s. Error: %s" % (self.es_type, e))
        return doc


    def _get_doc_field(self, doc, name):
        try:
            return doc[name]
        except ValueError as ve:
            print ("Error getting field %s from doc type %s" % (name, self.es_type))
            raise ve

    def _find_matching_predicate(self, obj):
        #looks for membership of lowercase name in one of the fields in the schema
        name = obj.get("type")
        for field in self.schema_obj.get("fields"):
            test = field.get("name", "").lower()
            if name.lower() in test:
                if "jsonldPredicate" in field.keys():
                    #matches and is an ID, good enough for us!
                    return {"field_name": field.get("name")}
        raise ValueError("No matching field found for name %s in type " % (name, self.es_type))

    def _find_geopoints(self, obj):
        res = {"field_name": "location"}
        for field in self.schema_obj.get("fields"):
            test = field.get("name", "").lower()
            if test in ["lat", "latitude"]:
                res["lat"] = field.get("name")
            elif test in ["lon", "lng", "long", "longitude"]:
                res["lon"] = field.get("name")
        if not "lat" and "lon" in res:
            raise ValueError("Couldn't resolve geopoints for field %s of type %s" % ("location", self.es_type))
        return res


if __name__ == "__main__":

    manager = ESConsumerManager()
    print ("Started!")
    while True:
        try:
            pass
            Sleep(10)
        except KeyboardInterrupt as e:
            print("\nTrying to stop gracefully")
            manager.stop()
            break

