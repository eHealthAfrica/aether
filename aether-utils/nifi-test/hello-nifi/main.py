import json
import requests
from aether.client import KernelClient

from post import url, data, send
from assets import project_obj, mapping_obj, project_schema_obj, schema_obj, kernel_url, kernel_credentials


def pprint(obj):
    print(json.dumps(obj, indent=2))

def register():
    client = KernelClient(kernel_url, **kernel_credentials)
    project = client.Resource.Project.add(project_obj)
    project_id = project.get("id")
    schema = client.Resource.Schema.add(schema_obj)
    schema_id = schema.get("id")
    project_schema_obj['project'] = project_id
    project_schema_obj['schema'] = schema_id
    project_schema = client.Resource.ProjectSchema.add(project_schema_obj)
    project_schema_id = project_schema.get("id")
    mapping_obj["definition"]["entities"]["Clinic"] = project_schema_id
    mapping_obj["project"] = project_id
    mapping = client.Resource.Mapping.add(mapping_obj)
    pprint(mapping)
    return mapping.get("id")

def post_test():
    client = KernelClient(kernel_url, **kernel_credentials)
    endpoint = client.Submission.get("hfr")
    raw_payload = '''{"id":"cefc7405-3ec9-4ca8-bbe7-54fd53f05eb4","type":"Feature","geometry":{"type":"Point","coordinates":[-11.57633994,7.92979802]},"properties":{"name":"Gerihun","alternate_name":"Not Available","facility_type":{"code":"SLE-3","label":"Community Health Center","description":null},"location":{"code":"92656","name":"Boama","location_type":{"code":"SLE_4","name":"Sierra Leone Admin Level 4","administrative_level":4}},"description":"","rating":null,"date_created":"2016-11-02","last_updated":"2017-11-21","location__parent__parent__name":"Southern","location__parent__parent__parent__code":"sl","location__parent__parent__parent__name":"Sierra Leone","location__parent__code":"31115","location__parent__name":"Bo","location__parent__parent__code":"2657"}}'''
    payload = json.loads(raw_payload)
    data = {
        "revision" : 1,
        "map_revision": 1,
        "payload": payload
    }
    res = endpoint.submit(data)
    pprint(res)


if __name__ == "__main__":
    _id = register()
    data["mapping"] = _id
    send(url, data)
