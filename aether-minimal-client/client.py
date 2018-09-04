import coreapi
from coreapi.codecs import JSONCodec
import json
from openapi_codec import OpenAPICodec



class Client(object):

    def __init__(self):
        decoders = [OpenAPICodec(), JSONCodec()]

        user = 'admin'
        pw = 'adminadmin'
        url = 'http://kernel.aether.local/v1/schema/?format=openapi'

        auth = coreapi.auth.BasicAuthentication(user, pw)
        self.client = coreapi.Client(auth=auth, decoders=decoders)
        self.schema= self.client.get(url)

    def get_matching(self, _type, start_page=1, sort_on='modified', filter_params={}):
        if _type not in self.schema.keys():
            raise ValueError("No matching type: %s in API" % _type)
        if 'list' not in self.schema[_type]:
            raise ValueError('No list function for type %s' % _type)
        fields = [i.name for i in self.schema[_type]['list'].fields]
        params = filter_params
        if sort_on in fields:
            params['ordering'] = sort_on
        for key in [i for i in params.keys()]:
            if not key in fields:
                del params[key]
        page = start_page
        _next = True
        while _next:
            params['page'] = page
            entities = self.client.action(self.schema, [_type, 'list'], validate=False, params=params)
            _next = entities.get('next')
            page += 1
            results = entities.get('results')
            for item in results:
                yield(item)


client = Client()

params = {"projectschema":"caf6da3c-cf37-4493-aa7b-6aa0e95d53e4"}

for x, i in enumerate(client.get_matching('entities', sort_on='id', filter_params=params)):
    print(x)
    print(json.dumps(i, indent=2))



