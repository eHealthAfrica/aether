from . import api


def walk_changes(db, f, *args, **kwargs):
    supplied_params = kwargs.get('params', {})
    # set some defaults
    params = {'since': 0, 'limit': 100}
    params.update(supplied_params)
    # loop and fetch changes until the end of the changes has been reached
    while True:
        ks = kwargs.copy()
        ks.update({'params': params})
        r = api.get(db + '/_changes', *args, **ks)
        r.raise_for_status()
        j = r.json()
        cs = j['results']
        done = len(cs) == 0 or len(cs) < params['limit']
        for c in cs:
            f(c)
        if done:
            break
        params.update({'since': j['last_seq']})


def force_put_doc(path, document):
    doc = document.copy()
    r = api.get(path)
    if r.status_code == 404:
        # the doc does not exist
        pass
    else:
        r.raise_for_status()
        j = r.json()
        if '_rev' in j:
            doc['_rev'] = j['_rev']
    r = api.put(path, json=doc)
    r.raise_for_status()
    return r


def fetch_dbs_info():
    r = api.get('_all_dbs')

    # get the list of non-private databases
    dbs = [db for db in r.json() if not db.startswith('_')]

    # create the dict of existing and valid databases with info
    results = {}
    for dbname in dbs:
        db = api.get(dbname)
        db.raise_for_status()
        results[dbname] = db.json()
    return results


def fetch_db_docs(dbname, last_seq):
    '''
    get all changed documents in the database since last sequence
    '''
    changes_url = '{}/_changes?style=all_docs&include_docs=true&since={}'.format(dbname, last_seq)

    r = api.get(changes_url)
    r.raise_for_status()
    result = r.json()
    return {
        'last_seq': result['last_seq'],
        'docs': [doc['doc'] for doc in result['results']],
    }
