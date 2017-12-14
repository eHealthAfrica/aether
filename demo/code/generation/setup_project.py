import json
import random
import sys
import os.path
import requests

from generate import loadSchemas


ODK_URL = None
ODK_USR = None
ODK_PW = None
BASE_URL = None
CORE_USR = None
CORE_PW = None

with open("./server_settings.json") as f:
    S = json.load(f)
    ODK_URL = S['odk-url']
    ODK_USR = S['odk-usr']
    ODK_PW = S['odk-pw']
    BASE_URL = S['core-url']
    CORE_USR = S['core-usr']
    CORE_PW = S['core-pw']
    


SCHEMAS = {}
PROJECT_SCHEMAS = {}
PROJECT_ID = None
MAPPING_ID = None

def postProject():
    package = {
        "revision": "1",
        "name": "nov-demo",
        "salad_schema": "[]",
        "jsonld_context": "[]",
        "rdf_definition": "[]"
    }
    url = "%s/projects/" % (BASE_URL)
    return post(url, package)


def postSchema(doc):
    package = {
        "name": doc.get("name"),
        "type": doc.get("type"),
        "revision": "1", 
        "definition": json.dumps(doc)
    }
    url = "%s/schemas/" % (BASE_URL)
    return post(url, package)

def postProjectSchema(schemaID, schemaName):
    package = {
        "revision": "1", 
        "schema":schemaID,
        "name": schemaName,
        "project": PROJECT_ID, 
        "masked_fields": "[]", 
        "transport_rule": "[]", 
        "mandatory_fields": "[]"
    }
    url = "%s/projectschemas/" % (BASE_URL)
    return post(url, package)

def postMapping(projectID):
    data = None
    with open("../form-mapping.json") as f:
        data = f.read()
        data = data.replace("UUID_LOC", "\"" + PROJECT_SCHEMAS['Location'] + "\"");
        data = data.replace("UUID_PER", "\"" + PROJECT_SCHEMAS['Person'] + "\"");
        data = data.replace("UUID_HHLD", "\"" + PROJECT_SCHEMAS['Household'] + "\"");
    package = {
        "name": "test",
        "definition": data,
        "revision": "1",
        "project": projectID
    }
    url = "%s/mappings/" % (BASE_URL)
    return post(url, package)
    
def addODKUser():
    package = {
        "username": "dave",
        "password": "adminadmin"
    }
    url = "%s/surveyors/" % (ODK_URL)
    return postODK(url, package)

def postODKSurvey(mapping_id, user_id):
    package = {
        "mapping_id": mapping_id,
        "surveyors": [user_id],
        "name": "demo"
    }
    url = "%s/surveys/" % (ODK_URL)
    return postODK(url, package)

def postODKForm(user_id, survey_id):
    data = None
    with open("../xform/form1.xml") as f:
        data = f.read()
    package ={
        "surveyors": [user_id],
        "xml_file": None,
        "xml_data": data,
        "description": "demo survey",
        "created_at": None,
        "survey": survey_id
    }
    url = "%s/xforms/" % (ODK_URL)
    return postODK(url, package)

        

def post(url, package):
    auth = requests.auth.HTTPBasicAuth(CORE_USR,CORE_PW)
    req = requests.post(url, auth=auth, data=package)
    return json.loads(req.text)

def postODK(url, package):
    auth = requests.auth.HTTPBasicAuth(ODK_USR,ODK_PW)
    req = requests.post(url, auth=auth, data=package)
    return json.loads(req.text)


def registerSchemas():
    print ("registering schemas")
    resp = postProject()
    print("PROJCT resp\n %s" % json.dumps(resp , indent=2))
    global PROJECT_ID, PROJECT_SCHEMAS, MAPPING_ID
    PROJECT_ID = resp.get("id")
    with open("../all_schemas.json") as f:
        schemas = json.load(f)
        for obj in schemas:
            name = obj.get('name')
            schema = obj
            #print("posting\n %s" % json.dumps(obj , indent=2))
            resp = postSchema(schema)
            print("SCHEMA resp\n %s" % json.dumps(resp , indent=2))
            schema_id = resp.get("id")
            schema_name = resp.get("name")
            SCHEMAS[name] = schema_id
            #print("posting\n %s" % json.dumps(schema_id , indent=2))
            resp = postProjectSchema(schema_id, schema_name)
            print("PS resp\n %s" % json.dumps(resp , indent=2))
            schema_id = resp.get("id")
            PROJECT_SCHEMAS[name] = schema_id

        resp = postMapping( PROJECT_ID )
        print("MAPPING resp\n %s" % json.dumps(resp , indent=2))
        MAPPING_ID = resp.get("id")
        resp = addODKUser()
        print("USER resp\n %s" % json.dumps(resp , indent=2))
        USER_ID = resp.get("id")
        resp = postODKSurvey(MAPPING_ID, USER_ID)
        print("SURVEY resp\n %s" % json.dumps(resp , indent=2))
        resp = postODKForm(USER_ID, MAPPING_ID)
        print("XFORM resp\n %s" % json.dumps(resp , indent=2))

        with open("./gen_cache.json", "w") as f:
            data = {
                "schemas": SCHEMAS,
                "project_schemas": PROJECT_SCHEMAS,
                "project_id": PROJECT_ID }
            print (json.dumps(data, indent=2))
            json.dump(data, f)

if __name__ == "__main__":
    if loadSchemas():
        sys.exit("Cached schemas [./gen_cache.json] exists, exiting")
    registerSchemas()
    print ("schemas registered! You can now generate")


