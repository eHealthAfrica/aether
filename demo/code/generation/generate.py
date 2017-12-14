import json
import random
import sys
import os.path
import requests

version = 3
try:
    import urllib.request
except Exception:
    print ("REQUIRES PYTHON3, use pipenv --three")
    sys.exit(255)
    version = 2
    

from avro.io import Validate
from avro.schema import Parse
from uuid import uuid4

#list of section_ids
SECTIONS = ["2","3","4"]
HOUSEHOLDS = []

#generator objects are on global scope
PERSON_GEN = None
PLACE_GEN = None
LOC_GEN = None

#const
CREATION_MAX = 10000 # number of person entities to create

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

def postEntity(doc, entity_type):
    schema_id = PROJECT_SCHEMAS.get(entity_type)
    package = {
        "id": doc.get("id"),
        "revision": "1", 
        "payload": json.dumps(doc), 
        "projectschema": schema_id, 
        "status":"Publishable"
    }
    url = "%s/entities/" % (BASE_URL)
    print("posting package: %s" % json.dumps(package, indent=2))
    return post(url, package)


def post(url, package):
    auth = requests.auth.HTTPBasicAuth(CORE_USR,CORE_PW)
    req = requests.post(url, auth=auth, data=package)
    return json.loads(req.text)


def loadSchemas():
    cache_path = "./gen_cache.json"
    if not os.path.isfile(cache_path):
        return False
    with open(cache_path, "r") as f:
        cache = json.load(f)
        global SCHEMAS, PROJECT_SCHEMAS, PROJECT_ID
        SCHEMAS = cache.get("schemas")
        PROJECT_SCHEMAS = cache.get("project_schemas")
        PROJECT_ID = cache.get("project_id")    
        print ("Loaded Cache")
        return True

#generator wrapper with DB interaction for entity gen
def entityGenerator( name, gen_func ):
    db = None
    schema = None
    with open("../all_schemas.json") as f:
        schemas = json.load(f)
        for obj in schemas:
            if str(obj.get('name')) == name:
               schema = Parse(json.dumps(obj))
               break
    count = 0
    while True:
        count+=1
        doc = gen_func()
        if not validEntity(doc,schema):
            print("%s, failed validation!" % name)
            print(json.dumps(doc, indent=2))
            break
        print (json.dumps(postEntity(doc, name), indent=2))
        yield doc.get("id")
        print ("Created %s #%s" % (name, count) )

#validate generated entities against avro schema
def validEntity(doc, schema):
    valid = Validate(schema, doc)
    return valid

#base doc definition
def baseDoc():
    doc = {"id": str(uuid4())}
    return doc
    
#household entity

def genHousehold():
    doc = baseDoc()
    HOUSEHOLDS.append(doc.get('id'))
    doc["sectionID"] = random.choice(SECTIONS)
    doc["locationID"] = next(LOC_GEN)
    doc["headOfHouseHold"] = next(PERSON_GEN)
    doc["hasBedNets"] = random.choice([True, False])
    size = random.randint(0,10)
    for i in range(size):
        next(PERSON_GEN)
    return doc
        

#person entity
def genPerson():
    doc = baseDoc()
    data = getData()
    doc['firstName'] = "%s" % (data.get("name", {}).get("first"))
    doc['lastName'] = "%s" % (data.get("name", {}).get("last"))
    doc['age'] = random.randint(1,99)
    doc['isAlive'] = True if random.randint(1,99) < 85 else False
    doc['householdID'] = HOUSEHOLDS[-1]
    return doc

#location entity
def genLoc():
    doc = baseDoc()
    #location precision and bounding box
    precision = .000001
    lat_min, lat_max = 5.938235 , 15.530767
    lng_min, lng_max = -13.600614, 15.107004
    #random point in box
    doc['lat'] = ( random.randint(int(lat_min / precision), int(lat_max / precision))* precision )
    doc['lng'] = ( random.randint(int(lng_min / precision), int(lng_max / precision))* precision )
    return doc

#pull a random name/dob/placename from an existing random source
def getData():
    data = None
    url = "https://randomuser.me/api/"
    if version == 3:
        req = urllib.request.Request(url, data, {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as f:
            response = f.read()
            encoding = f.info().get_content_charset('utf-8')
            return json.loads(response.decode(encoding)).get("results")[0]
    else:
        response = urllib2.urlopen(url)
        return json.load(response).get("results")[0]   

   

#main generation loop
def generate():
    #inst generators and db instance
    global PERSON_GEN, HOUSEHOLD_GEN, LOC_GEN
    PERSON_GEN = entityGenerator("Person", genPerson)
    HOUSEHOLD_GEN = entityGenerator("Household", genHousehold)
    LOC_GEN = entityGenerator("Location", genLoc)
    for i in range(CREATION_MAX):
        next(HOUSEHOLD_GEN)


if __name__ == "__main__":
    if not loadSchemas():
        sys.exit("Schemas are not registered, run setup_project.py first")
    generate()


