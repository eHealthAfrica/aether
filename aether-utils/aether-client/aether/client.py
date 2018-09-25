import coreapi
from coreapi.codecs import JSONCodec
from openapi_codec import OpenAPICodec
import requests


class Client(object):

    def __init__(self, url, user, pw):
        self.user = user
        self.pw = pw
        self.kernel_url = url
        self.schema_url = '%s/v1/schema/?format=openapi' % self.kernel_url
        auth = coreapi.auth.BasicAuthentication(self.user, self.pw)
        decoders = [OpenAPICodec(), JSONCodec()]
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        self.client = coreapi.Client(auth=auth, decoders=decoders, session=session)
        self.schema = self.client.get(self.schema_url)

    # UTILITIES

    def validate_call(self, data_type, remote_function, sort_on=None, validate_params={}):
        if data_type not in self.schema.keys():
            raise ValueError("No matching type: %s in API" % data_type)
        if remote_function not in self.schema[data_type]:
            raise ValueError('No %s function for type %s' %
                             (remote_function, data_type))
        fields = [i.name for i in self.schema[data_type]
                  [remote_function].fields]
        params = dict(validate_params)
        if sort_on and sort_on in fields:
            params['ordering'] = sort_on
        if params:
            for key in [i for i in params.keys()]:
                if key not in fields:
                    del params[key]
        return params

    def list_types(self):
        return self.schema.keys()

    def get_functions_for_type(self, data_type):
        if not self.schema.get(data_type):
            raise ValueError("No matching type: %s in API" % data_type)
        return self.schema[data_type]

    # CREATE

    def create(self, data_type, obj):
        remote_function = 'create'
        params = self.validate_call(
            data_type, remote_function, validate_params=obj)
        return self.client.action(
            self.schema, [data_type, remote_function], validate=False, params=params)

    # READ

    def get_single(self, data_type, _id):
        _iter = self.get(data_type, filter_params={
            'id': _id
        })
        result = list(_iter)
        if not result:
            raise ValueError(
                'No matching result in type %s for ID %s' % (data_type, _id))
        if len(result) > 1:
            raise ValueError(
                'More than one result in type %s for ID %s' % (data_type, _id))
        return result[0]

    def get_count(self, data_type, filter_params={}):
        return self._count_paginated(data_type, filter_params)

    def get(self, data_type, start_page=1, sort_on='modified', filter_params={}):
        remote_function = 'list'
        return self._paginated(data_type, remote_function, start_page, sort_on, filter_params)

    def _count_paginated(self, data_type, filter_params={}):
        remote_function = 'list'
        params = self.validate_call(
            data_type, remote_function, validate_params=filter_params)
        entities = self.client.action(
            self.schema, [data_type, remote_function], validate=False, params=params)
        return entities.get('count')

    def _paginated(
            self, data_type, remote_function,
            start_page=1, sort_on='modified', filter_params={}):

        params = self.validate_call(
            data_type, remote_function, sort_on, filter_params)
        page = start_page
        _next = True
        while _next:
            params['page'] = page
            entities = self.client.action(
                self.schema, [data_type, remote_function], validate=False, params=params)
            _next = entities.get('next')
            page += 1
            results = entities.get('results')
            if not results:
                raise StopIteration
            for item in results:
                yield(item)

    '''
    There is a bug in the COREAPI Transport layer that affects the following methods.
    If there are two methods to access the same variable (id as both query and path),
    the URL becomes malformed. I've tried to reconstruct the Generated Fields to address
    this, but it's a) a huge fiddly pain b) doesn't work and c) create and read are what
    the API Client currently does the most of.
    '''

    # UPDATE

    def update(self, data_type, obj):
        raise NotImplementedError(
            'UPDATE is not well supported by COREAPI with this OpenAPICodec')

    def partial_update(self, data_type, url, updates):
        raise NotImplementedError(
            'PARTIAL_UPDATE is not well supported by COREAPI with this OpenAPICodec')

    # DELETE

    def delete(self, data_type, _id):
        raise NotImplementedError(
            'DELETE is not well supported by COREAPI with this OpenAPICodec')
