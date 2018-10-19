# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import collections
from collections import namedtuple
import json
import logging
from queue import Queue, Empty
import os
from random import randint, uniform, choice, sample
import signal
import string
from threading import Thread
from time import sleep
from uuid import uuid4

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from aether.client import Client


class Generic(object):
    '''
    We keep our default mocking functions for each type here as generic
    '''
    @staticmethod
    def boolean():
        return choice([True, False])

    @staticmethod
    def float():
        return uniform(.01, 1000.00)

    @staticmethod
    def int():
        return randint(1, 99999)

    @staticmethod
    def null():
        return None

    @staticmethod
    def string():
        size = choice(range(3, 12))
        return "".join(sample(string.ascii_lowercase, size))

    @staticmethod
    def uuid():
        return str(uuid4())

    @staticmethod
    def geo_lat():
        return uniform(0.00000000000, 60.00000000000)

    @staticmethod
    def geo_lng():
        return uniform(0.00000000000, 180.00000000000)


class DataMocker(object):
    '''
    An extensible tool that consumes an Avro Schema and creates junk data that matches it.
    Data generation methods can be overridden on a per type [text, int, etc] basis via:
        override_type(type_name, fn)
    Override methods can also be passed on a property name basis [lat, lon, name] via:
        override_property(property_name, fn)
    '''

    def __init__(self, name, schema, parent):

        self.MAX_ARRAY_SIZE = 4
        self.QUEUE_WORKERS = 10
        self.REUSE_COEFFICIENT = 0.85

        self.name = name
        self.raw_schema = schema
        self.parent = parent
        self.subschema = {}
        self.primative_types = [
            "null",
            "boolean",
            "int",
            "long",
            "float",
            "double",
            "bytes",
            "string"
        ]

        self.type_methods = {
            primative: MockFn(self._default(primative))
            for primative in self.primative_types
        }
        self.created = []  # ids of created entities
        self.reuse = 0  # number of recycled entity ids
        self.count = 0  # number of entity references to this type
        self.property_methods = {}
        self.required = []
        self.ignored_properties = []
        self.restricted_types = {}
        self.instructions = {}
        self.killed = False
        self._queue = Queue()
        self.__start_queue_process()
        self.override_property("id", MockFn(Generic.uuid))
        self.load()

    def _default(self, primative):
        if primative in ["int", "long"]:
            return Generic.int
        if primative in ["float", "double"]:
            return Generic.float
        if primative is "null":
            return Generic.null
        if primative is "string":
            return Generic.string
        if primative is "boolean":
            return Generic.boolean

    def kill(self):
        self.killed = True

    def __start_queue_process(self):
        for x in range(self.QUEUE_WORKERS):
            worker = Thread(target=self.__reference_runner, args=[])
            worker.daemon = False
            worker.start()

    def __reference_runner(self):
        while True:
            if self.killed:
                break
            try:
                fn = self._queue.get(block=True, timeout=1)
                fn()
            except Empty as emp:
                if self.killed:
                    break
                sleep(1)
            except Exception as err:
                raise err

    def get_reference(self, exclude=None):
        # called from other types to generate this one (lazily)
        # returns an ID, either of by registering a new instance
        # or by returning a value from created
        self.count += 1
        thresh = 0 if self.count <= 100 else (100 * self.REUSE_COEFFICIENT)
        new = (randint(0, 100) >= thresh)
        if new:
            _id = self.quick_reference()
        else:
            items = self.created[:-4]
            if items:
                self.reuse += 1
                _id = choice(items)
            else:
                _id = self.quick_reference()
        return _id

    def quick_reference(self):
        # generates an id for this type
        # queues a job to actually make the instance
        _id = None
        if self.property_methods.get('id'):
            fn = self.property_methods.get('id')
            _id = fn()
        else:
            fn = [fn for name, fn in self.instuctions.get(
                self.name) if name == 'id']
            if not fn:
                raise ValueError("Couldn't find id function")
            _id = fn[0]()
        deffered_generation = MockFn(self.fullfill_reference, [_id])
        self._queue.put(deffered_generation)
        return _id

    def fullfill_reference(self, _id):
        # the method called from the queue to create an instance
        new_record = self.get(set_id=_id)
        self.parent.register(self.name, new_record)
        return _id

    def get(self, record_type="default", set_id=None):
        # Creates a mock instance of this type
        # wraps _get
        if record_type is "default":
            body = self._get(self.name)
            if set_id:
                body['id'] = set_id
            self.created.append(body.get('id'))
            return body

        else:
            return self._get(record_type)

    def _get(self, name):
        # actually compiles the instruction set for this type and returns the body
        instructions = self.instructions.get(name)
        if not instructions:
            alt = self.parent.names.get(name)
            instructions = self.instructions.get(alt)
            if not instructions:
                raise ValueError("No instructions for type %s" % name)

        body = {}
        for name, fn in instructions:
            body[name] = fn()
        return body

    def gen(self, _type):
        # generation of avro types
        return self.type_methods.get(_type)

    def gen_array(self, _type):
        # generation of an array of any type
        fn = self.gen(_type)
        return MockFn(self._gen_array, [fn])

    def _gen_array(self, fn):
        size = choice(range(2, self.MAX_ARRAY_SIZE))
        return [fn() for i in range(size)]

    def gen_random_type(self, name=None, _types=None):
        if _types is None:
            _types = []
        return MockFn(self._gen_random_type, [name, _types])

    def _gen_random_type(self, name, types):
        # picks on of the valid types available for the field and completes it
        if name in self.required:
            types = [i for i in types if i != "null"]
        _type = choice(types)
        fn = None
        if isinstance(_type, dict):
            if _type.get("type", None) != "array":
                raise ValueError("unexpected type, %s" % _type.get('type'))
            items = _type.get("items")
            fn = self.gen_array(items)
            return fn()
        elif isinstance(_type, list):
            if name in self.required:
                _type = [i for i in _types if i != "null"]
            _type = choice(_type)
        if not _type in self.primative_types:
            fn = self.gen_complex(_type)
        else:
            fn = self.gen(_type)
        return fn()

    def gen_complex(self, _type):
        return MockFn(self._gen_complex, _type)

    def _gen_complex(self, name):
        # handles generation of associated types
        try:
            return self._get(name)
        except ValueError as verr:
            fn = self.gen("null")
            return fn()

    def gen_reference(self, name, _type, types):
        # gets a reference to a foreign type
        # usually triggers creation via the other types get_reference()
        return MockFn(self._gen_reference, [name, _type, types])

    def _gen_reference(self, name, _type, types):
        if name in self.required:
            types = [i for i in types if i != "null"]
        chosen = choice(types)
        if isinstance(chosen, str):
            return self.parent.get_reference(_type)
        else:
            size = choice(range(2, self.MAX_ARRAY_SIZE))
            return [self.get_reference(_type) for i in range(size)]

    def ignore(self, property_name):
        # turn off mocking for this property
        self.ignored_properties.append(property_name)

    def override_type(self, type_name, fn):
        # provide an override method for an avro type
        # fn is a MockFn object
        self.type_methods[type_name] = fn
        self.load()

    def override_property(self, property_name, fn):
        # overrides a property in this type by name with a new function
        # for example instead of returning a random string for the name field, pick for a list
        # fn is a MockFn object
        self.property_methods[property_name] = fn
        self.load()

    def load(self):
        # loads schema definition for this type
        self.schema = json.loads(self.raw_schema)
        if isinstance(self.schema, list):
            for obj in self.schema:
                self.parse(obj)
        else:
            self.parse(self.schema)

    def parse(self, schema):
        # looks at all the types called for
        # matches simple types to type_methods
        # stubs external calls to parent for linked types
        name = schema.get("name")
        instructions = []
        fields = schema.get("fields", [])
        for field in fields:
            instructions.append(self._comprehend_field(field))
        self.instructions[name] = instructions
        for i in self.instructions[name]:
            log.debug("Add instruction to %s : %s" % (name, i))

    def _comprehend_field(self, field):
        # picks apart an avro definition of a field and builds mocking functions
        name = field.get("name")
        if name in self.ignored_properties:
            return (name, self.gen("null"))  # Return null function and get out
        try:
            ref_type = field.get("jsonldPredicate").get("_id")
            types = field.get('type')
            # This is a reference property  # TODO THIS MIGHT WANT TO BE sub_type
            return (name, self.gen_reference(name, ref_type, types))
        except Exception as err:
            pass  # This is simpler than checking to see if this is a dictionary?
        if name in self.property_methods.keys():
            # We have an explicit method for this
            return (name, self.property_methods.get(name))
        types = field.get("type")
        if isinstance(types, str):
            return (name, self.gen(types))  # Single type for this field
        if name in self.restricted_types.keys():  # we've limited the types we want to mock
            types = list(set(types).union(
                set(self.restricted_types.get(name))))
        return tuple([name, self.gen_random_type(name, types)])

    def require(self, *property):
        # Make a field never resolve to null (if null is an option)
        if isinstance(property, list):
            self.required.extend(property)
        else:
            self.required.append(property)

    def restrict_type(self, property_name, allowable_types=None):
        # some properties can be completed by multiple types of properties
        # for example [null, int, string[]?].
        # restrict_type allows you to chose a subset of the permitted types for mocking
        if allowable_types is None:
            allowable_types = []
        self.restricted_types[property_name] = allowable_types


class MockFn(namedtuple("MockFn", ("fn", "args"))):
    # Function wrapper class containing fn and args

    def __new__(cls, fn, args=None):
        this = super(MockFn, cls).__new__(cls, fn, args)
        return this

    def __call__(self):
        if self.args and not isinstance(self.args, list):
            return self.fn(self.args)
        try:  # This lets us get very duck-type-y with the passed functions
            return self.fn(*self.args) if self.args else self.fn()
        except TypeError as terr:
            return self.fn(self.args)


class MockingManager(object):

    def __init__(self, kernel_url, user, pw):
        # connects to Aether and gets available schemas.
        # constructs a DataMocker for each type
        
        self.client = Client(kernel_url, user, pw)
        self.types = {}
        self.alias = {}
        self.names = {}
        self.project_schema = {}
        self.schema_id = {}
        self.type_count = {}
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        self.load()


    def get(self, _type):
        if not _type in self.types.keys():
            msg = "No schema for type %s" % (_type)
            log.error(msg)
            raise KeyError(msg)
        return self.types.get(_type).get()

    def get_reference(self, _type):
        if not _type in self.types.keys():
            msg = "No schema for type %s" % (_type)
            log.error(msg)
            raise KeyError(msg)
        return self.types.get(_type).get_reference()

    def kill(self, *args, **kwargs):
        for name, mocker in self.types.items():
            log.info("Stopping thread for %s" % name)
            mocker.kill()

    def register(self, name, payload=None):
        # register an entity of type 'name'
        # if no payload is passed, an appropriate one will be created
        count = self.type_count.get(name, 0)
        count += 1
        self.type_count[name] = count
        if not payload:
            payload = self.types[name].get()
        type_name = self.alias.get(name)
        type_id = self.schema_id.get(name)
        ps_id = self.project_schema.get(type_id)
        data = self.payload_to_data(ps_id, payload)
        res = self.client.entities.create(data=data)
        log.debug("Created instance # %s of type %s" % (self.type_count[name], name))
        return data


    def payload_to_data(self, ps_id, payload):
        # wraps data in expected aether jargon for submission
        data = {
            "id": payload['id'],
            "payload": payload,
            "projectschema": ps_id,
            "mapping_revision": "None",
            "status": "Publishable"
        }
        return data

    def load(self):
        # loads schemas and project schemas from aether client
        log.debug("Loading schemas from Aether Kernel")
        for schema in self.client.schemas.paginated('list'):
            name = schema.name
            log.debug("Loading schema for type %s \n%s" % (name, schema))
            _id = schema.id
            definition = schema.definition
            if isinstance(definition, str):
                definition = json.loads(definition)
            if isinstance(definition, list):
                full_name = [obj.get("name") for obj in definition if obj.get(
                    'name').endswith(name)][0]
            else:
                full_name = definition.get('name')
                namespace = definition.get('namespace')
                if namespace:
                    if not name in namespace:
                        full_name = namespace+"."+name
            self.types[full_name] = DataMocker(
                full_name, json.dumps(definition), self)
            self.names[name] = full_name
            self.names[full_name] = name
            self.types[name] = self.types[full_name]
            self.alias[full_name] = name
            self.alias[name] = full_name
            self.schema_id[name] = _id
            self.schema_id[full_name] = _id
            self.schema_id[_id] = name

        for ps in self.client.projectschemas.paginated('list'):
            schema_id = ps.schema
            _id = ps.id
            self.project_schema[schema_id] = _id
            self.project_schema[_id] = schema_id
