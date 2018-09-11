from datetime import datetime, timedelta
import json
import time
from random import randint, choice


_letters = "abcdefghij"
facilities = ["facility_%s" % x.upper() for x in _letters]
max_stock = {'facility_H': 806, 'facility_I': 432, 'facility_J': 403, 'facility_D': 642, 'facility_E': 845, 'facility_F': 759, 'facility_G': 828, 'facility_A': 119, 'facility_B': 307, 'facility_C': 649}
antigens = [
    'IPV',
    'DTPHibHepB',
    'Measles',
    'Rubella',
    'Rotavirus',
    'Pneumo',
    'BCG'
]

_ids = {'facility_H': '17f78fd4-df56-4a6e-8b75-0d032da13da4', 'facility_I': '5a6e268f-4a3b-400d-ba16-b71aee41bd9b', 'facility_J': 'a5ace4ab-8c74-47e0-a4e5-b9c06b4b7260', 'facility_D': '751e6cb5-8c99-4b7a-a291-b2fd06413bce', 'facility_E': 'bc0830d2-e639-43a3-9032-d7e4798f63fa', 'facility_F': 'd12a3a4a-b505-4e11-bee6-5c63edba94eb', 'facility_G': 'c2ca16a2-c257-4b33-8b5c-fb6a4cb827af', 'facility_A': 'b874c9bc-f154-4df1-9b6f-60913babfee7', 'facility_B': '527095a9-2f77-43c6-9c4c-ed74ff6c7346', 'facility_C': 'ef960467-81bc-4d11-9c13-ce2fc2547cf7'}

def date_iter(_str):
    fmt = '%Y-%m-%d'
    d = datetime.strptime(_str, fmt)
    inc =  timedelta(days=1)
    while True:
        if d.weekday() <5:
            yield format_date(d)
        d += inc

def format_date(dt):
    return dt.isoformat()[:10]


def get_level(f, last):
    sign = choice([-1, 1])    
    change = int(randint(0, 20) * .01 * sign * max_stock[f])
    res = max_stock[f] if last + change > max_stock[f] else last + change
    if res < 0:
        res = 0
    return res


def reports(start):
    levels = { n : { a : randint(0, max_stock[n]) for a in antigens} for n in facilities}
    dates = date_iter(start)
    while True:
        _date = next(dates)
        for n in levels:
            doc = {
                'facility_id' : _ids[n],
                'facility_name' : n,
                'report_datetime' : _date,
                'levels' : {}
            }

            for a in levels[n]:
                levels[n][a] = get_level(n, levels[n][a])

            doc['levels']['vaccines'] = [{'type': k, 'count': v } for k,v in levels[n].items()]
            yield(doc)

def pprint(obj):
    print(json.dumps(obj, indent=2))

r = reports('2017-01-01')

from client import Client

c = Client('http://kernel.aether.local', 'admin', 'adminadmin')

submissions = []

start = time.time()

for x in range(1000):
    payload = next(r)
    obj = {
        'mapping' : 'afb4922c-dff2-44f0-a194-a978de4970aa',
        'payload' : payload
    }
    submissions.append(payload)
    #res = c.create('submissions', obj)
    print(x)

end = time.time()

print("1000 in %s seconds" % (end - start))

with open('./submissions_1000.json', 'w') as f:
    json.dump(submissions, f)



            
