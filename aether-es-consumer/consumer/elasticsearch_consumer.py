import ast
import os
import io
import json
import sys
import threading
import signal
import avro.schema
import avro.io

from avro.datafile import DataFileReader
from avro.io import DatumReader

from time import sleep as Sleep
from aether.client import KernelClient
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError, ConflictError
from kafka import KafkaConsumer

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
CONN_RETRY = 3
CONN_RETRY_WAIT_TIME = 10


#Default Kafka Port
KAFKA_HOST = "kafka:29092"  # from outside of docker it's kafka.aether.local:29092

#Default Kernel Credentials
kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

#Global Elasticsearch Connection
es = None
#Global Kernel Connection
kernel = None

def pprint(obj):
    print(json.dumps(obj, indent=2))

def connect():
    connect_aether()
    connect_kafka()
    connect_es()


def connect_aether():
    for x in range(CONN_RETRY):
        try:
            global kernel
            kernel = KernelClient(url= "http://kernel.aether.local:8000", **kernel_credentials)
            return
        except Exception as ke:
            #TODO find proper Exception type
            kernel = None
            print ("Error initializing connection to Aether: %s" % ke)
            Sleep(CONN_RETRY_WAIT_TIME)
    print("Failed to connect to Aether after %s retries" % CONN_RETRY)
    sys.exit(1) # Kill consumer with error

def connect_es():
    for x in range(CONN_RETRY):
        try:
            global es
            es = Elasticsearch(["localhost", "elasticsearch"],sniff_on_start=False) #default connection on localhost
            print (es.info())
            return
        except TransportError as ese:
            print("Could not connect to Elasticsearch Instance")
            Sleep(CONN_RETRY_WAIT_TIME)
    print("Failed to connect to ElasticSearch after %s retries" % CONN_RETRY)
    sys.exit(1) # Kill consumer with error

def connect_kafka():
    for x in range(CONN_RETRY):
        try:
            consumer = KafkaConsumer(
                group_id='test-loaded',
                bootstrap_servers=['kafka:29092'],
                auto_offset_reset='earliest'
            )
            print(consumer.topics())
            print("Connected to Kafka...")
            return
        except Exception as ke:
            print("Could not connect to Kafka: %s" % (ke))
            Sleep(CONN_RETRY_WAIT_TIME)
    print("Failed to connect to Kafka after %s retries" % CONN_RETRY)
    sys.exit(1) # Kill consumer with error


class ESConsumerManager(object):

    def __init__(self):
        self.stopped = False
        signal.signal(signal.SIGINT, self.stop) #SIGTERM should kill subprocess via manager.stop()
        signal.signal(signal.SIGTERM, self.stop)
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

    def stop(self, *args, **kwargs):
        self.stopped = True
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
        self.consumer_timeout = 1000  #MS
        self.consumer_max_records = 1000
        self.group_name = "elastic_%s_%s" % (self.index, self.es_type)
        self.sleep_time = 10
        self.stopped = False
        self.consumer = None
        super(ESConsumer, self).__init__()

    def connect(self):
        try:
            self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_HOST,
                                         group_id=self.group_name,
                                         heartbeat_interval_ms=2500,
                                         session_timeout_ms=18000,
                                         request_timeout_ms=20000,
                                         auto_offset_reset='latest',
                                         consumer_timeout_ms=17000)
            self.consumer.subscribe([self.topic])
            self.seek_to_beginning(self.consumer)  # TODO KILL
            return True
        except Exception as ke:
            print ("%s failed to subscibe to topic %s with error \n%s" % (self.index, self.topic, ke))
            return False

    def seek_to_beginning(self, consumer):
        consumer.poll(timeout_ms=100, max_records=1)  #we have to poll to get the right partitions assigned to the consumer
        consumer.seek_to_beginning()

    def run(self):
        while True:
            if self.connect():
                break
            elif self.stopped:
                return
            Sleep(10)
        total_wait = 0
        while True:
            last_offset = None
            partitioned_messages = self.get_records()
            if partitioned_messages:
                total_wait = 0
                last_schema = None
                for part, packages in partitioned_messages.items():  # we don't worry about the partitions for now
                    for package in packages: # a package can contain multiple messages serialzed with the same schema
                        schema = None
                        obj = io.BytesIO()
                        obj.write(package.value)
                        reader = DataFileReader(obj, DatumReader())

                        # We can get the schema directly from the reader.
                        # we get a mess of unicode that can't be json parsed so we need ast
                        raw_schema = ast.literal_eval(str(reader.meta))
                        schema = raw_schema.get("avro.schema")
                        if not schema:
                            raise AttributeError("No Schema!")
                        if schema != last_schema:
                            self.processor.load_avro(schema)
                            self.processor.load()  # create a process pipeline based on the new schema
                            print(schema)
                        '''
                        except Exception as err:
                            print(err)
                        '''

                        for x, msg in enumerate(reader):
                            # do something with the individual messages
                            # print("processing message #%s from package" % (x))
                            doc = self.processor.process(msg)
                            self.submit(doc)
                        last_offset = package.offset
                        last_schema = schema
                        obj.close()  # don't forget to close your open IO object.
                if last_offset:
                    print("index: %s -> %s offset: %s" % (self.index, self.topic, last_offset))
            else:
                total_wait += self.consumer_timeout
                print("consumer group %s has no new messages available, waiting %s ms." % (self.group_name, self.consumer_timeout))
                print("%s ms since last message received..." % total_wait)
            if self.stopped:
                break
            else:
                Sleep(self.sleep_time)

        print ("Shutting down consumer %s | %s" % (self.index, self.topic))
        self.consumer.close()
        return

    def submit(self, doc):
        parent = doc.get("_parent", None)
        if parent: #parent can only be in metadata apparently
            del doc['_parent']
        try:
            es.create(
                index = self.index,
                doc_type = self.es_type,
                id = doc.get('id'),
                parent = parent,
                body = doc
            )
        except Exception as ese:
            print("Couldn't create doc because of error: %s\nAttempting update." % ese)
            try:
                es.update(
                    index = self.index,
                    doc_type = self.es_type,
                    id = doc.get('id'),
                    parent = parent,
                    body = doc
                )
                print("Success!")
            except TransportError as te:
                print("conflict exists, ignoring document with id %s" % doc.get("id", "unknown"))

    def get_records(self):
        messages = self.consumer.poll(timeout_ms=self.consumer_timeout, max_records=self.consumer_max_records)
        return messages

    def stop(self):
        print ("%s caught stop signal" % (self.group_name))
        self.stopped = True

class ESItemProcessor(object):

    def __init__(self, type_name, type_instructions):
        self.pipeline = []
        self.schema = None
        self.schema_obj = None
        self.schema_obj_all = None
        self.es_type = type_name
        self.type_instructions = type_instructions
        self.topic_name = type_name
        '''
        self.get_avro()
        self.load(type_instructions)
        '''

    def deserialize(self, doc):
        bytes_reader = io.BytesIO(doc.value)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)
        doc = reader.read(decoder)
        return doc

    def load_avro(self, schema_obj):
        try:
            self.schema = avro.schema.parse(schema_obj)
            self.schema_obj = json.loads(str(schema_obj))
            self.schema_obj_all = json.loads(str(schema_obj))
            self.schema_obj = [schema for schema in self.schema_obj if schema.get("name").endswith(self.es_type)][0]
        except Exception as ave:
            print ("Error parsing Avro schema for type %s" % self.es_type)
            raise ave

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
            print ("""No registered schema in Aether looks like indexed type: %s.
                The messages must be serialized with a schema""" % self.es_type)
            # raise TypeError("No registered schema in Aether looks like indexed type: %s" % self.es_type)

    def load(self):
        self.pipeline = []
        for key, value in self.type_instructions.items():
            print("process : %s | %s" % (key, value))
            if key in ["_parent", "_child"]:
                res = {"function": "_add%s" % key}
                res.update(self._find_matching_predicate(value))
                self.pipeline.append(res)
            elif key == "properties":
                if "location" in value.keys():
                    res = {"function": "_add_geopoint"}
                    res.update(self._find_geopoints(value))
                    self.pipeline.append(res)

    def process(self, doc, schema=None):
        # doc = self.deserialize(doc) #TODO switch based on presence of a schema
        for instr in self.pipeline:
            doc = self.exc(doc, instr)
        return doc

    def exc(self, doc, instr):
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
        doc = json.loads(json.dumps(doc))
        try:
            if name in doc.keys():
                return doc[name]
            else:
                keys = []
                bad = []
                for key in doc.keys():
                    val = doc.get(key)
                    try:
                        if name in val.keys():
                            return val.get(name)
                    except Exception as err:
                        pass
            pprint(doc)
            raise ValueError()
        except ValueError as ve:
            print ("Error getting field %s from doc type %s" % (name, self.es_type))
            raise ve

    def _find_matching_predicate(self, obj):
        #looks for membership of lowercase name in one of the fields in the schema
        name = obj.get("type")
        for schema in self.schema_obj_all:
            for field in schema.get("fields"):
                test = field.get("name", "").lower()
                if name.lower() in test:
                    if "jsonldPredicate" in field.keys():
                        #matches and is an ID, good enough for us!
                        return {"field_name": field.get("name")}
        raise ValueError("No matching field found for name %s in type %s" % (name, self.es_type))

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

def main_loop():
    connect()
    manager = ESConsumerManager()
    print ("Started!")
    while True:
        try:
            pass
            if not manager.stopped:
                Sleep(10)
            else:
                print("Manager caught SIGTERM, exiting")
                break
        except KeyboardInterrupt as e:
            print("\nTrying to stop gracefully")
            manager.stop()
            break



if __name__ == "__main__":
    main_loop()

