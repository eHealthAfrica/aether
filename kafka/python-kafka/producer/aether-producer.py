import json
import psycopg2
import avro.schema
import io
import ast

from avro.io import DatumWriter
from kafka import KafkaProducer
from aether.client import KernelClient
from psycopg2.extras import DictCursor
from time import sleep as Sleep

OFFSET_PATH = "./offset.json"
KAFKA_SERVER = 'localhost:29092'

jdbc_connection_string = "jdbc:postgresql://db:5432/aether?user=postgres"
jdbc_user = "postgres"

SLEEP_TIME = 10 #seconds between looking for changes

kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}
try:
    kernel = KernelClient(url= "http://kernel.aether.local:8000", **kernel_credentials)
except Exception as e:
    kernel = None
    print ("Error initializing connection to Aether: %s" % e)
    raise e

postgres_connection_info = {
    "user" : "postgres",
    "dbname" : "aether",
    "port" : 5432,
    "host" : "localhost"
}

def pprint(obj):
    print(json.dumps(obj, indent=2))

def set_offset_value(key, value):
    offsets = {}
    try:
        with open(OFFSET_PATH) as f:
            offsets = json.load(f)
            try:
                offsets[key] = value
                print ("set offset for %s : %s" % (key, value))
            except TypeError as te:
                offsets = {key: value}
    except IOError as ioe:
        offsets = {key: value}
    with open (OFFSET_PATH, "w") as f:
        json.dump(offsets, f)

def get_offset(key):
    try:
        with open(OFFSET_PATH) as f:
            offsets = json.load(f)
            try:
                return offsets[key]
            except ValueError as e:
                None
    except IOError as ioe:
        return None

def count_since(offset=None):
    if not offset:
        offset = ""
    with psycopg2.connect(**postgres_connection_info) as conn:
        cursor = conn.cursor(cursor_factory=DictCursor)
        count_str = '''
            SELECT
                count(CASE WHEN e.modified > '%s' THEN 1 END) as new_rows
            FROM kernel_entity e;
        ''' % (offset)
        cursor.execute(count_str);
        for row in cursor:
            return row.get("new_rows")

def get_entities(offset = None):
    if not offset:
        offset = ""
    conn = psycopg2.connect(**postgres_connection_info)
    cursor = conn.cursor(cursor_factory=DictCursor)
    query_str = '''
        SELECT
            e.id,
            e.revision,
            e.payload,
            e.modified,
            e.status,
            ps.id as project_schema_id,
            ps.name as project_schema_name,
            s.name as schema_name,
            s.id as schema_id,
            s.revision as schema_revision
                from kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE e.modified > '%s'
        ORDER BY e.modified ASC;
    '''  % (offset)
    cursor.execute(query_str)
    for row in cursor:
        yield {key : row[key] for key in row.keys()}


class KafkaStream(object):
    def __init__(self, topic, kernel):
        self.topic = topic
        self.kernel = kernel
        #connect to Server
        self.producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, acks=1)
        self.get_avro()
        print ("Connected to stream for topic: %s" % self.topic)

    def send(self, row):
        msg = row.get("payload")
        offset = row.get("modified")
        try:
            writer = avro.io.DatumWriter(self.schema)
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(msg, encoder)
            raw_bytes = bytes_writer.getvalue()
            self.producer.send(self.topic, key=msg.get("id"), value=raw_bytes)
            set_offset_value("entities", offset)

        except Exception as e:
            print ("Issue with Topic %s : %s" % (self.topic, e))
            raise e

    def get_avro(self):
        #Gets avro schema used for encoding messages
        #TODO Fix issue with json coming from API Client being single quoted
        definition = ast.literal_eval(str(self.kernel.Resource.Schema.get(self.topic).definition))
        self.schema = avro.schema.Parse(json.dumps(definition))

    def stop(self):
        self.producer.flush()
        self.producer.close()

class StreamManager(object):

    def __init__(self, kernel):
        self.kernel = kernel
        self.streams = {}
        self.start()

    def start(self):
        self.kernel.refresh()
        topics = self.kernel.Resource.Schema
        for topic in topics:
            self.streams[topic.name] = KafkaStream(topic.name, self.kernel)

    def send(self, row_generator):
        for row in row_generator:
            topic = row.get("schema_name")
            self.streams[topic].send(row)
        print ("manager finished processing changes")

    def stop(self):
        for name, stream in self.streams.items():
            stream.stop()
            print ("released connection to topic: %s" % name)
        self.streams = {}
        print ("manager stopped")

if __name__ == "__main__":
    manager = None
    try:
        while True:
            offset = get_offset("entities")
            new_items = count_since(offset)
            if new_items:
                print ("Found %s new items, processing" % new_items)
                entities = get_entities(offset)
                manager = StreamManager(kernel)
                manager.send(entities)
                manager.stop()
                manager = None
            else:
                print ("No new items. Offset is %s, sleeping for %s s" % (offset, SLEEP_TIME))
                Sleep(SLEEP_TIME)
    except KeyboardInterrupt as e:
        print ("Caught Keyboard interrupt")
        if manager:
            print ("Trying to kill manager")
            manager.stop()
