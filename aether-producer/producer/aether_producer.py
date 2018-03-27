import json
import psycopg2
import avro.schema
import io
import ast
import os
import signal
import sys

from avro.io import DatumWriter
from avro.datafile import DataFileWriter
from kafka import KafkaProducer
from aether.client import KernelClient
from psycopg2.extras import DictCursor
from time import sleep as Sleep

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = "%s/settings.json" % FILE_PATH
TEST_SETTINGS_FILE = "%s/test-settings.json" % FILE_PATH


class Settings(object):

    def __init__(self, test=False):
        if test:
            self.load(TEST_SETTINGS_FILE)
        else:
            self.load(SETTINGS_FILE)
    def load(self, path):
        with open(path) as f:
            obj = json.load(f)
            for k in obj:
                setattr(self, k, obj.get(k))
            self.offset_path = "%s/%s" % (FILE_PATH, self.offset_file)


'''
SETTINGS = load_settings(SETTINGS_FILE)

def init_settings(SETTINGS):
    global
    KAFKA_SERVER = SETTINGS.get('kafka_server')
    jdbc_connection_string = SETTINGS.get('jdbc_connection_string')
    jdbc_user = SETTINGS.get('jdbc_user')
    SLEEP_TIME = SETTINGS.get('sleep_time')  # seconds between looking for changes
    kernel_url = SETTINGS.get("kernel_url")
    kernel_credentials = SETTINGS.get('kernel_credentials')
    postgres_connection_info = SETTINGS.get('postgres_connection_info')
'''

def connect():
    try:
        kernel = KernelClient(url=_settings.kernel_url, **_settings.kernel_credentials)
        return kernel
    except Exception as e:
        kernel = None
        print ("Error initializing connection to Aether: %s" % e)
        raise e


def set_offset_value(key, value):
    offsets = {}
    try:
        with open(_settings.offset_path) as f:
            offsets = json.load(f)
            try:
                offsets[key] = value
            except TypeError as te:
                offsets = {key: value}
    except IOError as ioe:
        offsets = {key: value}
    with open (_settings.offset_path, "w") as f:
        json.dump(offsets, f)


def get_offset(key):
    try:
        with open(_settings.offset_path) as f:
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
    with psycopg2.connect(**_settings.postgres_connection_info) as conn:
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
    conn = psycopg2.connect(**_settings.postgres_connection_info)
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
        self.producer = KafkaProducer(bootstrap_servers=_settings.kafka_server, acks=1, key_serializer=str.encode)
        self.get_avro()
        print ("Connected to stream for topic: %s" % self.topic)


    def send(self, row):
        msg = row.get("payload")
        offset = row.get("modified")
        try:
            bytes_writer = io.BytesIO()
            writer = DataFileWriter(bytes_writer, DatumWriter(), self.schema, codec='deflate')
            writer.append(msg)
            writer.flush()
            raw_bytes = bytes_writer.getvalue()
            writer.close()
            future = self.producer.send(self.topic, key=str(msg.get("id")), value=raw_bytes)
            #block until it actually sends. We don't want offsets getting out of sync
            try:
                record_metadata = future.get(timeout=10)
            except Exception as ke:
                print ("Error submitting record")
                raise ke
            self.producer.flush()
            set_offset_value("entities", offset)

        except Exception as e:
            print ("Issue with Topic %s : %s" % (self.topic, e))
            raise e


    def get_avro(self):
        #Gets avro schema used for encoding messages
        #TODO Fix issue with json coming from API Client being single quoted
        definition = ast.literal_eval(str(self.kernel.Resource.Schema.get(self.topic).definition))
        self.schema = avro.schema.parse(json.dumps(definition))


    def stop(self):
        self.producer.flush()
        self.producer.close()


class StreamManager(object):


    def __init__(self, kernel):
        self.killed = False
        signal.signal(signal.SIGINT, self.kill) #SIGTERM ends run
        signal.signal(signal.SIGTERM, self.kill)
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
            if self.killed: #look for sigterm
                print ("manager stopped in progress via signal")
                return
            topic = row.get("schema_name")
            self.streams[topic].send(row)
        print ("manager finished processing changes")


    def stop(self):
        for name, stream in self.streams.items():
            stream.stop()
            print ("released connection to topic: %s" % name)
        self.streams = {}
        print ("manager stopped")

    def kill(self):
        self.killed = True

def main_loop(test=False):
    global _settings
    _settings = Settings(test)
    manager = None
    kernel = None
    for x in range(3):
        try:
            kernel = connect()
            break
        except Exception as err:
            Sleep(SETTINGS.get("start_delay", 5))
    if not kernel:
        sys.exit(1)
    print("Producer Connected to Aether.")
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
                if manager.killed:
                    print("processed stopped by SIGTERM")
                    break
                manager = None
            else:
                Sleep(_settings.sleep_time)
    except KeyboardInterrupt as ek:
        print ("Caught Keyboard interrupt")
        if manager:
            print ("Trying to kill manager")
            manager.stop()
    except Exception as e:
        print(e)
        if manager:
            manager.stop()

if __name__ == "__main__":
    main_loop()
