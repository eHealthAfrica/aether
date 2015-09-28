import fileinput
for line in fileinput.input():
    process(line)

def walk(d):
    ret = {}
    if 'children' in d:
        ret = {}
        ret["properties"] = dict((c['name'], walk(c)) for c in d['children'])
    _type = d.get('type', None)
    if _type == 'string':
        ret = {}
        ret['type'] = 'string'
        ret['description'] = d['label']
    return ret

