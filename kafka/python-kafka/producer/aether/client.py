import json
import requests

class GenericClient(object):

    _default_url = None
    _resource_types = {}
    _data_types = {}

    def __init__(self, url=None, **credentials):
        if not url:
            self.url_base = _default_url
        else:
            self.url_base = url
        if not 'username' and 'password' in credentials.keys():
            raise KeyError("Credentials 'username' and 'password' required")
        self.auth = requests.auth.HTTPBasicAuth(credentials.get('username'), credentials.get('password'))
        try:
            self.refresh()
        except Exception as e:
            print ("Could not connect to server: error %s" % e)


    def refresh(self):
        self.__dict__['Resource'] = DottedDict()
        resource = self.__dict__['Resource']
        for key, name in self._resource_types.items():
            resource[key] = ResourceCollection(name, self)


    def get(self, url):
        req = requests.get(url, auth=self.auth)
        return req.json()

    def post(self, url, data):
        req = requests.post(url, auth=self.auth, data=data)
        return json.loads(req.text)

    def put(self, url, data):
        req = requests.put(url, auth=self.auth, data=data)
        return json.loads(req.text)

class KernelClient(GenericClient):

    _default_url = "http://kernel.aether.local:8000"

    _resource_types = {
        "Project" : "projects",
        "Mapping" : "mappings",
        "Schema" : "schemas",
        "ProjectSchema" : "projectschemas"
    }

    _data_types = {
        "Submission" : "submissions",
        "Entity" : "entities"
    }

    def refresh(self):
        super(KernelClient, self).refresh()
        self.__dict__["Submission"] = SubmissionsCollection("submissions", self)
        tree = {"projectschemas_url":{"entities_url":None}}
        self.__dict__['Entity'] = ResourceDataTree("entities", self, tree, url="/schemas/")
        return


class ODKModuleClient(GenericClient):

    _default_url = "odk.aether.local:8443"
    _resource_types = {
        "Survey" : "surveys",
        "XForm" : "xforms",
        "Surveyor" : "surveyors"
    }

class DottedDict(dict):

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

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
        return json.dumps(self.info(), indent=2)

    def info(self):
        return {
            "type": self.name,
            "size": self.size()
        }

    def size(self):
        return len(self.resources)


class ResourceDataTree(GenericCollection):

    def __init__(self, collection_name, client, tree, url=None):
        super(ResourceDataTree, self).__init__(collection_name, client)
        self.tree = tree
        if len(url)< 4 or url[:4] != "http":
            self.url = self.client.url_base + url
        else:
            self.url = url
        self.load()

    def load(self):
        key = list(self.tree.keys())[-1]
        next_tree = self.tree.get(key)
        body = self.client.get(self.url)
        results = body.get('results')
        for block in results:
            _id = block.get('id')
            name = block.get('name')
            if name:
                self.name_alias[_id] = name
                self.name_alias[name] = _id
            else:
                name = _id
            if isinstance(next_tree, dict):
                #another level to the tree
                url = block.get(key)
                res = ResourceDataTree(name, self.client, next_tree, url=url)
            else:
                url = block.get(key)
                res = EntityData(name, url, self.client)
            self.resources[_id] = res
            self.order.append(_id)

    def info(self):
        return {
            "type": self.name,
            "size": self.size(),
            "entries": dict(self.name_alias.items())
        }

    def __getattr__(self, key):
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key):
        value = self.resources.get(key)
        if not value:
            alias = self.name_alias.get(key)
            return self.resources.get(alias, None)
        return value



class ResourceCollection(GenericCollection):

    def __init__(self, collection_name, client):
        super(ResourceCollection, self).__init__(collection_name, client)
        self.url = (self.client.url_base + self._url_pattern) % self.name
        self.load()

    def __iter__(self):
        return iter(self.resources.values())

    def load(self):
        self.resources, self.name_alias, self.order = ({},{},[])
        body = self.client.get(self.url)
        body = body.get('results')
        for item in body:
            res = Resource(item, self)
            self.order.append(res.id)
            self.resources[res.id] = res
            try:
                self.name_alias[res.name] = res.id
                self.name_alias[res.id] = res.name
            except Exception as e:
                print (e)

    def __getattr__(self, key):
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key):
        value = self.resources.get(key)
        if not value:
            alias = self.name_alias.get(key)
            return self.resources.get(alias, None)
        return value

    def search(self, terms):
        results = []
        for item in self:
            for term in terms:
                if item.info(term) != terms[term]:
                    break
                results.append(item)
        return results


    def names(self):
        return iter(self.name_alias.keys())

    def ids(self):
        return iter(self.order)

    def add(self, json_body=None, json_file=None):
        #json_file takes presidence
        if json_file:
            with open(json_file) as f:
                json_body = json.load(f)
        return self.client.post(self.url, json_body)

    def update(self, resource):
        url = self.url+"%s/" % resource.name
        body = resource.data
        #for some reason we have to first string out the JSON here for json fields
        if body.get('definition'):
            body['definition'] = json.dumps(body.get('definition'))
        return self.client.put(url, body)


class Resource(object):

    def __init__(self, raw, collection):
        self.data = raw
        self.collection = collection

    def __getattr__(self, key):
        if key == "collection":
            return self.collection
        return self.data.get(key)

    def __setattr__(self, name, value):
        if not name in ["data", "collection"]:
            self.data[name] = value
        else:
            super(Resource, self).__setattr__(name, value)

    def __str__(self):
        try:
            return json.dumps(self.info(), indent=2)
        except TypeError as e:
            return str(self.info())

    def info(self, term=None):
        if term and self.data.get(term):
            return self.data.get(term)
        return self.data


    def update(self):
        response = self.collection.update(self)
        if response:
            return response #print (json.dumps(response, indent=2))


class DataEndpoint(object):

    def __init__(self, client, url=None):
        self.client = client
        self.url = url

    def submit(self, data):
        return self.client.post(self.url, data)

    def get_instances(self, filter=None):
        #iterates over pages
        #optional filter function
        #TODO Add a skip or offset parameter
        url = self.url
        while True:
            payload = self.client.get(url)
            results = payload.get('results')
            for item in results:
                if filter:
                    if filter(item):
                        yield item
                else:
                    yield item
            if payload.get("next") != None:
                url = payload.get("next")
            else:
                raise StopIteration
    def __str__(self):
        return json.dumps(self.info(), indent =2)

    def info(self):
        return {}


class EntityData(DataEndpoint):

    def __init__(self, name, url, client):

        self.client = client
        self.url = url
        self.name = name
        super(EntityData, self).__init__(self.client, self.url)

    def get(self):
        pass

    def info(self, term):
        obj = {
            "type": "entity_endpoint",
            "projectschema_name": self.name,
            "url": self.url
        }

        if term and obj.get(term):
            return obj.get(term)
        return obj


class SubmissionData(DataEndpoint):

    def __init__(self, mapping_id, collection):
        self.collection = collection
        self.client = self.collection.client
        self.mapping_id = mapping_id
        self._url_pattern = "/mappings/%s/submissions/"
        self.url = (self.client.url_base + self._url_pattern) % mapping_id
        super(SubmissionData, self).__init__(self.client, self.url)

    def get(self):
        pass

    def __str__(self):
        return json.dumps(self.info(), indent =2)

    def info(self):
        return {
            "type": "submission_endpoint",
            "mapping_id": self.mapping_id,
            "mapping_name" : self.collection.name_alias.get(self.mapping_id),
            "url": self.url
        }


class SubmissionsCollection(GenericCollection):

    def __init__(self, collection_name, client):
        super(SubmissionsCollection, self).__init__(collection_name, client)
        self.url = (self.client.url_base + self._url_pattern) % self.name
        self.load()

    def __iter__(self):
        return iter(self.resources.keys())

    def load(self):
        self.resources, self.name_alias, self.order = ({},{},[])
        mapping = self.client.Resource.Mapping
        self.name_alias = mapping.name_alias
        for name in mapping.name_alias.keys():
            _id = self.name_alias.get(name)
            self.resources[name] = SubmissionData(_id, self)

    def __getattr__(self, key):
        res = self.get(key)
        if res:
            return res
        raise AttributeError("No attribute %s" % key)

    def get(self, key):
        value = self.resources.get(key)
        if not value:
            alias = self.name_alias.get(key)
            return self.resources.get(alias, None)
        return value

    def names(self):
        return iter(self.name_alias.keys())

    def ids(self):
        return iter(self.order)
