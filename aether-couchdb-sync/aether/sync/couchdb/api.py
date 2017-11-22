import requests
from django.conf import settings

'''
thin wrapper on top of requests for convenient calls to couchdb
'''

url = settings.COUCHDB_URL
defaults = {'auth': (settings.COUCHDB_USER, settings.COUCHDB_PASSWORD)}


def get(path, *args, **kwargs):
    # ks = {**defaults, **kwargs}
    # http://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.get(url + '/' + path, *args, **ks)


def head(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.get(url + '/' + path, *args, **ks)


def post(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.post(url + '/' + path, *args, **ks)


def put(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.put(url + '/' + path, *args, **ks)


def delete(path, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.delete(url + '/' + path, **ks)
