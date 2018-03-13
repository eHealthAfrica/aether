import collections
from collections import namedtuple
import json
from random import randint, uniform, choice, sample
import string
from uuid import uuid4

from aether.client import KernelClient

class Recurse(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

def recurse(*args, **kwargs):
    raise Recurse(*args, **kwargs)

def tail_recursive(f):
    def decorated(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except Recurse as r:
                args = r.args
                kwargs = r.kwargs
                continue
    return decorated

class Generic(object):

    @staticmethod
    def boolean():
        return choice([True, False])

    @staticmethod
    def float():
        return uniform(.01, 1000.00)

    @staticmethod
    def int():
        return randint(1,99999)

    @staticmethod
    def null():
        return None

    @staticmethod
    def string():
        size = choice(range(3,12))
        return "".join(sample(string.ascii_lowercase, size))

    @staticmethod
    def uuid():
        return str(uuid4())

    @staticmethod
    def geo_lat():
        return uniform(0.00000000000, 60.00000000000)

    @staticmethod
    def geo_lng():
        return uniform(0.00000000000, 60.00000000000)

class DataMocker(object):
    '''
    An extensible tool that consumes an Avro Schema and creates junk data that matches it.
    Data generation methods can be overridden on a per type [text, int, etc] basis via:
        override_type(type_name, fn)
    Override methods can also be passed on a property name basis [lat, lon, name] via:
        override_property(property_name, fn)
    '''

    def __init__(self, name, schema, parent):

        self.MAX_ARRAY_SIZE = 6

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
            primative : MockFn(self._default(primative))
            for primative in self.primative_types
        }
        self.created = []
        self.property_methods = {}
        self.required = []
        self.ignored_properties = []
        self.restricted_types = {}
        self.instructions = {}
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

    def get_reference(self, exclude=None):
        # returns an ID, either of by registering a new instance
        # or by returning a value from created

        count = len(self.created)
        print(self.name, count)
        thresh = 0 if count <= 5 else 90
        new = (randint(0,100) >= thresh)
        if new:
            new_record = self.get()
            self.parent.register(self.name, new_record)
            _id = new_record.get("id")
        else:
            _id = choice(self.created[:-5])
        return _id

    def get(self, record_type="default"):
        # Creates a mock instance.
        if record_type is "default":
            body = self._get(self.name)
            self.created.append(body.get('id'))
            return body

        else:
            return self._get(record_type)

    def _get(self, name):
        instructions = self.instructions.get(name)
        if not instructions:
            raise ValueError("No instuctions for type %s" % name)
        body = {}
        for name, fn in instructions:
            # print("\n%s*** ||| %s" % (name, fn))
            body[name] = fn()
        return body

    def _dispatch_complex(self, name):
        try:
            return self._get(name)
        except ValueError as verr:
            fn = self.gen("null")
            return fn()

    def gen(self, _type):
        return self.type_methods.get(_type)

    def gen_array(self, _type):
        fn = self.gen(_type)
        return MockFn(self._gen_array, [fn])

    def gen_random_type(self, name=None, _types=[]):
        return MockFn(self._gen_random_type, [name, _types])

    def _gen_random_type(self, name, types):
        if name in self.required:
            types = [i for i in types if i != "null"]
        _type = choice(types)
        # print("%s ---> %s" % (types, _type))
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
        # print(fn)
        return fn()

    def _gen_array(self, fn):
        size = choice(range(2,self.MAX_ARRAY_SIZE))
        return [fn() for i in range(size)]

    def gen_complex(self, _type):
        return MockFn(self._dispatch_complex, _type)

    def gen_reference(self, name, _type, types):
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
        self.type_methods[type_name] = fn
        self.load()

    def override_property(self, property_name, fn):
        self.property_methods[property_name] = fn
        self.load()

    def load(self):
        self.schema = json.loads(self.raw_schema)
        for obj in self.schema:
            self.parse(obj)

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

    def _comprehend_field(self, field):
        name = field.get("name")
        if name in self.ignored_properties:
            return (name, self.gen("null"))  # Return null function and get out
        try:
            ref_type = field.get("jsonldPredicate").get("_id")
            types = field.get('type')
            return (name, self.gen_reference(name, ref_type, types))  # This is a reference property  # TODO THIS MIGHT WANT TO BE sub_type
        except Exception as err:
            pass  # This is simpler than checking to see if this is a dictionary?
        if name in self.property_methods.keys():
            return (name, self.property_methods.get(name))  # We have an explicit method for this
        types = field.get("type")
        if isinstance(types, str):
            return (name, self.gen(types))  # Single type for this field
        if name in self.restricted_types.keys():  # we've limited the types we want to mock
            types = list(set(types).union(set(self.restricted_types.get(name))))
        return tuple([name, self.gen_random_type(name, types)])

    def require(self, *property):
        # Make a field never resolve to null (if null is an option)
        if isinstance(property, list):
            self.required.extend(property)
        else:
            self.required.append(property)


    def restrict_type(self, property_name, allowable_types=[]):
        # some properties can be completed by multiple types of properties
        # for example [null, int, string[]?].
        # restrict_type allows you to chose a subset of the permitted types for mocking
        self.restricted_types[property_name] = allowable_types


class MockFn(namedtuple("MockFn", ("fn", "args"))):
    # Function wrapper class containing fn and args

    def __new__(cls, fn, args=None):
        this = super(MockFn, cls).__new__(cls, fn, args)
        return this

    @tail_recursive
    def __call__(self):
        if self.args and not isinstance(self.args, list):
            return self.fn(self.args)
        try:  # This lets us get very duck-type-y with the passed functions
            return self.fn(*self.args) if self.args else self.fn()
        except TypeError as terr:
            return self.fn(self.args)

class MockingManager(object):

    def __init__(self):
        # connects to Aether and gets available schemas.
        # constructs a DataMocker for each type
        kernel_url = "http://kernel.aether.local:8000/v1"
        kernel_credentials ={
            "username": "admin-kernel",
            "password": "adminadmin",
        }
        self.client = KernelClient(kernel_url, **kernel_credentials)
        self.types = {}
        self.load()

    def get(self, _type):
        if not _type in self.types.keys():
            raise KeyError("No schema for type %s" % (_type))
        return self.types.get(_type).get()

    def get_reference(self, _type):
        if not _type in self.types.keys():
            raise KeyError("No schema for type %s" % (_type))
        return self.types.get(_type).get_reference()

    def register(self, name, payload):
        # pprint(payload)
        pass

    def load(self):
        for schema in self.client.Resource.Schema:
            name = schema.get("name")
            definition = schema.get('definition')
            full_name = [obj.get("name") for obj in definition if obj.get('name').endswith(name)][0]
            self.types[full_name] = DataMocker(full_name, json.dumps(definition), self)

def pprint(obj):
    print(json.dumps(obj, indent=2))
