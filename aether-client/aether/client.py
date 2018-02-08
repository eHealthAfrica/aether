import json
import requests


class GenericClient(object):
    '''Base client type to be subclassed.

    Holds access to http requests
    '''
    _default_url = None
    _resource_types = {}
    _type_lookup = {}
    _holds_resources = {}
    _data_types = {}

    def __init__(self, url=None, **credentials):
        self.url_base = url
        if not credentials:
            raise KeyError("No credentials passed!")
        creds = credentials.keys()
        if 'username' not in creds or 'password' not in creds:
            raise KeyError("Credentials 'username' and 'password' required")
        self.auth = requests.auth.HTTPBasicAuth(
            credentials.get('username'),
            credentials.get('password'))
        self.refresh()

    def refresh(self):
        self.__dict__['Resource'] = DottedDict()
        resource = self.__dict__['Resource']
        for key, name in self._resource_types.items():
            resource[key] = ResourceCollection(name, self)

    def delete(self, url):
        req = None
        try:
            req = requests.delete(url, auth=self.auth)
            ok = req.status_code in [requests.codes.ok, requests.codes.no_content]
        except requests.exceptions.ConnectionError:
            ok = False
        return {
            "ok": ok,
            "result": req
        }

    def get(self, url):
        req = requests.get(url, auth=self.auth)
        try:
            return req.json()
        except Exception as jse:
            ok = req.status_code in [requests.codes.ok, requests.codes.no_content]
            if not ok:
                return None
            return req.text  # TODO TEST

    def post(self, url, data):
        req = requests.post(url, auth=self.auth, data=data)
        return json.loads(req.text)

    def put(self, url, data):
        req = requests.put(url, auth=self.auth, data=data)
        return json.loads(req.text)


class KernelClient(GenericClient):
    '''Kernel API client class
    '''

    _default_url = "http://kernel.aether.local:8000"
    _resource_types = {
        "Project": "projects",
        "Mapping": "mappings",
        "Schema": "schemas",
        "ProjectSchema": "projectschemas"
    }

    _searchable_types = [
        "projects",
        "mappings",
        "projectschemas",
        "submissions",
        "schemas"
    ]

    _type_lookup = {v: k for k, v in _resource_types.items()}
    _holds_resources = {
        "mappings": "Submission"
    }

    def refresh(self):
        ''' Refreshes all Resource assets. Should be used sparingly.
        Better to call refresh on the asset directly instead of updating
        the entire tree.
        '''
        super(KernelClient, self).refresh()
        self.__dict__["Entity"] = EntityResolver(
            "resolver",
            self,
            KernelClient._searchable_types
        )
        self.__dict__["Submission"] = SubmissionsCollection("submissions", self)


class ODKModuleClient(GenericClient):
    '''ODK Module API client class

    Only has resouce types as the ODK module passes all entities
    and submissions to the Kernel.
    '''

    _default_url = "odk.aether.local:8443"
    _resource_types = {
        "Survey": "surveys",
        "XForm": "xforms",
        "Surveyor": "surveyors"
    }


class DottedDict(dict):
    '''A simple way to add JSON like .write access to python dictionaries
    '''

    def __setitem__(self, key, value):
        super(DottedDict, self).__setitem__(key, value)
        self.__dict__.update({key: value})


class GenericCollection(object):

    def __init__(self, collection_name, client):
        self._url_pattern = "/%s/"
        self.resources = {}
        self.name_alias = {}
        self.order = []
        self.name = collection_name
        self.client = client

    def __str__(self):
        return json.dumps(self.info(), indent=2)  # TODO TEST

    def info(self):
        return {  # TODO TEST
            "type": self.name,
            "size": self.size()
        }

    def size(self):
        return len(self.resources)  # TODO TEST


class EntityResolver(GenericCollection):
    '''Finds instance of entity based on a containing type.

    This class allows the generation of an EntityData endpoint that's limited by
    a group of entities relationships with another type.
    '''

    def __init__(self, collection_name, client, tree=None):
        super(EntityResolver, self).__init__(collection_name, client)
        self.tree = tree

    def resolve(self, value=None, filter_func=None):
        entity_url = "%s/entities/%s" % (self.client.url_base, value)
        resolver = EntityData(
            self.name,
            entity_url,
            self.client
        )
        if not resolver.valid:
            pass  # We may need to note this status somehow in the future
        return resolver

    def pluck(self, key):
        url = "%s/entities/%s/" % (self.client.url_base, key)
        resolver = EntityData(
            self.name,
            None,
            self.client
        )
        return resolver.pluck(url)

    def info(self):  # TODO TEST
        return {
            "type": self.name
        }

    def __getitem__(self, key):
            return self.__getattr__(key)

    def __getattr__(self, key=None):
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key=None, filter_func=None, search_type=None):
        result = self.pluck(key)
        if result:
            return result  # TODO TEST
        alt_keys = self.get_alternative_keys(key=key, search_type=search_type)
        for alt_key in alt_keys:
            result = self.resolve(alt_key, filter_func)
            if result:
                return result
        return None  # TODO TEST

    def get_alternative_keys(self, key, search_type=None):
        names = [name for name in self.tree]
        lookup = self.client._type_lookup
        types = [lookup.get(name) for name in names if lookup.get(name)]
        matches = []
        match_string = "?%s=%s"
        for t in types:
            res = self.client.Resource.get(t).get(key)
            if res:
                match_type = self.client._resource_types.get(t)
                singular = match_type[:-1]
                if not search_type:  # TODO TEST
                    matches.append(match_string % (singular, res.id))
                elif search_type == singular:  # TODO TEST
                    matches.append(match_string % (singular, res.id))
        if not matches:
            matches.append(match_string % ("submission", key))
        return matches


class SubmissionsCollection(GenericCollection):
    '''A collection to hold and access submissions.

    Submissions are keyed by the mapping they were submitted to.
    '''

    def __init__(self, collection_name, client):
        super(SubmissionsCollection, self).__init__(collection_name, client)
        self.url = (self.client.url_base + self._url_pattern) % self.name
        self.load()

    def __iter__(self):
        return iter(self.resources.keys())  # TODO TEST

    def load(self):
        self.resources, self.name_alias, self.order = ({}, {}, [])
        mapping = self.client.Resource.Mapping
        self.name_alias = mapping.name_alias
        for mapping in mapping:
            _id = mapping.get("id")
            self.order.append(_id)
            name = mapping.get("name")
            res = SubmissionData(_id, self)
            self.resources[name] = res
            self.resources[_id] = res

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __getattr__(self, key):
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key=None):
        if not key:
            return self.resources
        value = self.resources.get(key)
        if not value:
            alias = self.name_alias.get(key)
            return self.resources.get(alias, None)
        return value

    def names(self):  # TODO TEST
        return iter(self.name_alias.keys())

    def ids(self):  # TODO TEST
        return iter(self.order)


class ResourceCollection(GenericCollection):
    '''A collection type for 'Resources' types; [Project, Mapping, Schema, ProjectSchema]
    '''

    def __init__(self, collection_name, client):
        super(ResourceCollection, self).__init__(collection_name, client)
        self.url = (self.client.url_base + self._url_pattern) % self.name
        self.load()

    def __iter__(self):
        return iter(self.resources.values())

    def load(self):
        self.resources, self.name_alias, self.order = ({}, {}, [])
        url = self.url
        while True:
            body = self.client.get(url)
            results = body.get('results', None)
            if not results:  # TODO TEST
                return
            for item in results:
                res = Resource(item, self)
                self.order.append(res.id)
                self.resources[res.id] = res
                self.name_alias[res.name] = res.id
                self.name_alias[res.id] = res.name
            # Look for another page. If there isn't one, finish up.
            url = body.get("next", None)
            if not url:
                break

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __getattr__(self, key=None):  # TODO TEST
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key=None):
        if not key:  # TODO TEST
            return self.resources
        value = self.resources.get(key)
        if not value:
            alias = self.name_alias.get(key)
            value = self.resources.get(alias, None)
        return value

    def search(self, filter_func):
        for item in self:
            if filter_func(item):
                yield(item)

    def names(self):
        return iter(self.name_alias.keys())

    def ids(self):
        return iter(self.order)

    def add(self, json_body=None, json_file=None):
        # json_file takes presidence
        if json_file:  # TODO TEST
            with open(json_file) as f:
                json_body = json.load(f)
        definition = json_body.get('definition')
        if definition:
            if not isinstance(definition, str):
                json_body['definition'] = json.dumps(definition)
            else:
                json_body['definition'] = definition
        result = self.client.post(self.url, json_body)
        # we refresh our resources before we return
        self.load()
        if self.name in self.client._holds_resources.keys():
            name = self.client._holds_resources.get(self.name)
            self.client.__dict__.get(name).load()
        return result

    def delete(self, resource):
        _id = resource.get("id")
        if not _id:  # TODO TEST
            raise ValueError("Resource has no id field")
        uri = "%s%s" % (self.url, _id)
        response = self.client.delete(uri)
        self.load()
        return response

    def update(self, resource):
        url = self.url+"%s/" % resource.name
        body = resource.data
        # for some reason we have to first string out the JSON here for json fields
        definition = body.get('definition')
        if definition:
            if not isinstance(definition, str):  # TODO TEST
                body['definition'] = json.dumps(definition)
        result = self.client.put(url, body)
        self.load()
        return result


class Resource(object):
    '''Object to hold and modify Resource types. in ResourceCollection
    '''

    def __init__(self, raw, collection):
        self.data = raw
        self.collection = collection

    def __getattr__(self, key=None):
        if key == "collection":  # TODO TEST
            return self.collection
        if key not in self.data.keys():
            raise KeyError
        return self.data.get(key)

    def __getitem__(self, key):
            return self.__getattr__(key)

    def __setattr__(self, name, value):
        if name not in ["data", "collection"]:
            self.data[name] = value
        else:
            super(Resource, self).__setattr__(name, value)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __str__(self):
        try:
            return json.dumps(self.info(), indent=2)
        except TypeError as e:  # TODO TEST
            return str(self.info())

    def delete(self):
        return self.collection.delete(self)

    def get(self, key=None):
        if key:
            return self.__getattr__(key)
        else:  # TODO TEST
            return self.collection

    def info(self, term=None):
        if term and self.data.get(term):
            return self.data.get(term)
        return self.data

    def update(self):
        response = self.collection.update(self)
        if response:
            return response


class DataEndpoint(object):
    '''A generic supertype for managing data elements [Submission, Entity]

    Allows CRUD of data elements.
    Allows lazy loading of paginiated results, search via filter_func and plucking by id
    '''

    def __init__(self, client, url=None):
        self.client = client
        self.url = url
        self.valid = True
        if url:  # If instatiated with a search url, will flag invalid if there are no results.
            if not next(self.get_instances(self.url), None):
                self.valid = False

    def __iter__(self):
        return self.get_instances()

    def submit(self, url=None, data=None):
        payload = data.get("payload")
        if not isinstance(payload, str):
            data['payload'] = json.dumps(payload)
        return self.client.post(self.url, data)

    def update(self, url=None, data=None):
        if not url:  # TODO TEST
            url = self.url
        payload = data.get("payload")
        if not isinstance(payload, str):
            data['payload'] = json.dumps(payload)
        return self.client.put(url, data)

    def pluck(self, url):
        res = self.client.get(url)
        if res.get("detail") == "Not found.":
            return None
        return res

    def get_instances(self, url=None, filter_func=None):
        '''generated based method for getting instances from paginated results

        Iterates continously over returned pages. Optionally filtering from
        results with an aribrary passed function.
        '''
        # TODO Add a skip or offset parameter
        if not url:
            url = self.url
        while True:
            payload = self.client.get(url)
            if not payload:  # TODO TEST
                return None
            results = payload.get('results')
            if not results:
                raise StopIteration
            for item in results:
                if filter_func:
                    if filter_func(item):
                        yield item
                else:
                    yield item
            if payload.get("next") is not None:
                url = payload.get("next")
            else:
                raise StopIteration

    def __str__(self):  # TODO TEST
        return json.dumps(self.info(), indent=2)

    def info(self, term=None):  # TODO TEST
        return {"url": self.url}


class EntityData(DataEndpoint):
    '''DataEndpoint type for access and modification of Entities

    Currently only explicitly supports Read, Write and Update
    '''

    def __init__(self, name, url, client):
        self.client = client
        self.post_url = "%s/entities/" % self.client.url_base
        self.pluck_url = self.post_url+"%s/"
        if not url:
            self.url = self.post_url
        else:
            self.url = url
        self.name = name
        super(EntityData, self).__init__(self.client, self.url)

    def get(self, id=None, filter_func=None):
        if not id:
            return super(EntityData, self).get_instances(
                url=self.url,
                filter_func=filter_func)
        else:
            return super(EntityData, self).pluck(self.pluck_url % id)

    def submit(self, data=None):
        res = super(EntityData, self).submit(self.post_url, data)  # TODO TEST
        return res

    def update(self, data):
        url = data.get('url')
        if not url:
            raise AttributeError("url should have been present in pulled record")  # TODO TEST
        res = super(EntityData, self).update(url, data)
        return res

    def info(self, term=None):
        obj = {
            "type": "entity_endpoint",
            "projectschema_name": self.name,
            "url": self.url
        }

        if term and obj.get(term):  # TODO TEST
            return obj.get(term)
        return obj


class SubmissionData(DataEndpoint):
    '''DataEndpoint type for access and modification of Submissions

    Currently only explicitly supports Read and Write
    '''

    def __init__(self, mapping_id, collection):
        self.collection = collection
        self.client = self.collection.client
        self.mapping = self.client.Resource.Mapping.get(mapping_id)
        self._url_pattern = "/submissions/?mapping=%s"
        self.url = self.client.url_base+"/submissions/"
        self.pluck_url = self.url+"%s/"
        self.get_url = (self.client.url_base + self._url_pattern) % mapping_id
        super(SubmissionData, self).__init__(self.client, self.url)

    def get(self, id=None, filter_func=None):
        if not id:
            return super(SubmissionData, self).get_instances(
                url=self.url,
                filter_func=filter_func)
        else:
            return super(SubmissionData, self).pluck(self.pluck_url % id)

    def submit(self, data):
        if not data.get('mapping'):
            data['mapping'] = self.mapping.id
        res = super(SubmissionData, self).submit(self.url, data)
        self.collection.load()
        return res

    def __str__(self):
        return json.dumps(self.info(), indent=2)

    def info(self, term=None):
        return {
            "type": "submission_endpoint",
            "mapping_id": self.mapping_id,
            "mapping_name": self.collection.name_alias.get(self.mapping_id),
            "url": self.url
        }
