from collections import namedtuple

class DataMocker(object):
    '''
    An extensible tool that consumes an Avro Schema and creates junk data that matches it.
    Data generation methods can be overridden on a per type [text, int, etc] basis via:
        override_type(type_name, fn)
    Override methods can also be passed on a property name basis [lat, lon, name] via:
        override_property(property_name, fn)
    '''

    def __init__(self, schema):
        self.type_methods = {

        }
        self.property_methods = {}
        self.ignored_properties = []
        self.parse(schema)

    def get(self):
        # Creates a mock instance.
        pass

    def ignore(self, property_name):
        # turn off mocking for this property
        self.ignored_properties.append(property_name)

    def override_type(self, type_name, fn):
        self.type_methods[type_name] = fn

    def override_property(self, property_name, fn):
        self.property_methods[property_name] = fn

    def parse(self, schema):
        # sets self.name from schema
        # looks at all the types called for
        # matches simple types to type_methods
        # stubs external calls to parent for linked types

        pass

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
