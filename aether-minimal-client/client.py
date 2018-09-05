import coreapi
from coreapi.codecs import JSONCodec
from coreapi.document import Document, Link, Field
import json
from openapi_codec import OpenAPICodec


class Client(object):

    def __init__(self):
        decoders = [OpenAPICodec(), JSONCodec()]
        self.user = 'admin'
        self.pw = 'adminadmin'
        self.kernel_url = 'http://kernel.aether.local'
        self.schema_url = '%s/v1/schema/?format=openapi' % self.kernel_url
        auth = coreapi.auth.BasicAuthentication(self.user, self.pw)
        self.client = coreapi.Client(auth=auth, decoders=decoders)
        self.schema= self.client.get(self.schema_url)

    # VALIDATE / INFO

    def validate_call(self, data_type, remote_function, sort_on=None, validate_params={}):
        if data_type not in self.schema.keys():
            raise ValueError("No matching type: %s in API" % data_type)
        if remote_function not in self.schema[data_type]:
            raise ValueError('No %s function for type %s' % (remote_function, data_type))
        fields = [i.name for i in self.schema[data_type][remote_function].fields]
        params = dict(validate_params)  # Shallow copy
        if sort_on and sort_on in fields:
            params['ordering'] = sort_on
        if params:
            for key in [i for i in params.keys()]:
                if not key in fields:
                    del params[key]
        return params

    def list_types(self):
        return self.schema.keys()

    def get_functions_for_type(self, data_type):
        if not self.schema.get(data_type):
            raise ValueError("No matching type: %s in API" % data_type)
        return self.schema[data_type]

    # READ

    def get_single(self, data_type, _id):
        _iter = self.get(data_type, filter_params={
                'id': _id
            })
        result = list(_iter)
        if not result:
            raise ValueError('No matching result in type %s for ID %s' % (data_type, _id))
        if len(result) > 1:
            raise ValueError('More than one result in type %s for ID %s' % (data_type, _id))
        return result[0]

    def get_count(self, data_type, filter_params={}):
        return self._count_paginated(data_type, filter_params)

    def get(self, data_type, start_page=1, sort_on='modified', filter_params={}):
        remote_function = 'list'
        total = self._count_paginated(data_type, filter_params=filter_params)
        return self._paginated(data_type, remote_function, start_page, sort_on, filter_params)

    def _count_paginated(self, data_type, filter_params={}):
        remote_function = 'list'
        params = self.validate_call(data_type, remote_function, validate_params=filter_params)
        entities = self.client.action(self.schema, [data_type, remote_function], validate=False, params=params)
        return entities.get('count')

    def _paginated(self, data_type, remote_function, start_page=1, sort_on='modified', filter_params={}):
        params = self.validate_call(data_type, remote_function, sort_on, filter_params)
        page = start_page
        _next = True
        while _next:
            params['page'] = page
            entities = self.client.action(self.schema, [data_type, remote_function], validate=False, params=params)
            _next = entities.get('next')
            page += 1
            results = entities.get('results')
            if not results:
                raise StopIteration
            for item in results:
                yield(item)

    # CREATE

    def create(self, data_type, obj):
        remote_function = 'create'
        return self.client.action(self.schema, [data_type, remote_function], validate=False, params=obj)

    # UPDATE

    '''
    def update(self, data_type, obj):
        remote_function = 'update'
        link = { k: v for k,v in self.schema[data_type][remote_function].__dict__.items() if k != 'fields' and not k.startswith('_')}
        as_dict = [i._asdict() for i in self.schema[data_type][remote_function].fields]
        new_fields = []
        for field in as_dict[:]:
            if field.get('location') == 'query':
                field['location'] = 'body'
                if field['name'] == 'id':
                    continue
            new_fields.append(Field(**field))
        new_link = Link(fields=new_fields, **link)
        schema = { data_type : {remote_function : new_link}}
        for i in schema[data_type][remote_function].fields:
            print(i)
        params = obj
        pprint(params)
        return self.client.action(schema, [data_type, remote_function], validate=False, params=params, overrides={'url': obj['url']})  #

    def partial_update(self, data_type, url, updates):
        remote_function = 'partial_update'
        params = dict(updates)
        return self.client.action(self.schema, [data_type, remote_function], validate=False, params=params, encoding='application/x-www-form-urlencoded', overrides={'url': url})
    '''

    # DELETE

    def delete(self, data_type, _id):
        pass


def pprint(obj):
    print(json.dumps(obj, indent=2))

client = Client()

params = {}# {"projectschema":"caf6da3c-cf37-4493-aa7b-6aa0e95d53e4"}

'''
for x, i in enumerate(client.get('schemas', filter_params=params)):
    print(x)
    pprint(json.dumps(i, indent=2))
'''

bad_id = '337'
_id = 'e43886f4-1101-4c0b-8015-4af2a92b53e2'
project = list(client.get('projects'))[0]
pprint(project)

project['salad_schema'] = 'delta'

'''
pos = client.get_functions_for_type('projects')
pprint([(i, str(pos.get(i))) for i in pos])
'''

print(client.get_functions_for_type('projects'))

new_project = client.update('projects', project)
