from collections import namedtuple
import json
from random import randint, uniform, choice, sample
import string

class DataMocker(object):
    '''
    An extensible tool that consumes an Avro Schema and creates junk data that matches it.
    Data generation methods can be overridden on a per type [text, int, etc] basis via:
        override_type(type_name, fn)
    Override methods can also be passed on a property name basis [lat, lon, name] via:
        override_property(property_name, fn)
    '''

    def __init__(self, name, schema):

        self.name = name
        self.schema = schema
        self.subschema = {}
        primative_types = [
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
            for primative in primative_types
        }
        self.property_methods = {}
        self.ignored_properties = []
        self.restricted_types = {}
        self.instructions = {}
        self.load()

    def _default(self, primative):
        if primative in ["int", "long"]:
            return self._gen_int
        if primative in ["float", "double"]:
            return self._gen_float
        if primative is "null":
            return self._gen_null
        if primative is "string":
            return self._gen_string
        if primative is "boolean":
            return self._gen_boolean

    def get(self, record_type="default"):
        # Creates a mock instance.
        if record_type is "default":
            return _get(self.name)
        else:
            return _get(record_type)

    def _get(self, name):
        instructions = self.instructions.get(name)
        if not instructions:
            raise ValueError("No instuctions for type %s" % name)
        body = {}
        for name, fn in instuctions:
            body[name] = fn()
        return body


    def _gen_boolean(self):
        return choice([True, False])

    def _gen_float(self):
        return uniform(.01, 1000.00)

    def _gen_int(self):
        return randint(1,99999)

    def _gen_null(self):
        return None

    def _gen_string(self):
        size = choice(xrange(3,12))
        return "".join(sample(string.ascii_lowercase, size))

    def gen(self, _type):
        return self.type_methods.get(_type)

    def gen_array(self, _type):
        fn = self.gen(_type)
        return MockFn(self._gen_array, [fn])

    def gen_random_type(self, _types=[]):
        return MockFn(self._gen_random_type, [types])

    def _gen_random_type(self, types):
        _type = choice(types)
        if not isinstance(_type, string)
            if not _type.get("type", None) is "array":
                raise ValueError("unexpected type, %s" % _type.get('type'))
            items = _type.get("items")
            fn = self.gen_array(items)
            return fn()
        fn = self.gen(_type)
        return fn()

    def _gen_array(self, fn):
        size = choice(xrange(2,12))
        return [fn() for i in xrange(size)]

    def gen_complex(self, _type):
        return self.gen("int")  # TODO implement complex lookups

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
        self.schema = json.loads(schema)


    def parse(self, schema):
        # looks at all the types called for
        # matches simple types to type_methods
        # stubs external calls to parent for linked types
        name = schema.get("name")
        instructions = []
        fields = schema.get("fields", [])
        for field in fields:
            instructions.append(self._comprehend_field(field))

    def _comprehend_field(self, field):
        name = field.get("name")
        if name in self.ignored_properties:
            return tuple(name, self.gen("null"))  # Return null function and get out
        sub_type = None
        try:
            sub_type = field.get("jsonldPredicate", {}).get("_id")
            return tuple(name, self.gen_complex(name))  # This is a reference property
        except Exception as err:
            pass
        if name in self.property_methods.keys():
            return tuple(name, property_methods.get(name))  # We have an explicit method for this
        types = field.get("type")
        if isinstance(types, string):
            return tuple(name, self.gen(types))  # Single type for this field
        if name in self.restricted_types.keys():  # we've limited the types we want to mock
            types = list(set(types).union(set(self.restricted_types.get(name))))
        return tuple(name, self.gen_random_type(types))




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
        pass

    def proxy(self, proxy_type, reference_field):
        pass
