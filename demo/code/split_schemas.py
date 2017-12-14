import json

OUT_DIR = "./avro"
SRC = "./all_schemas.json"

def segment(path, out):
    data = []
    with open(path) as f:
        data = json.load(f)
    for schema in data:
        name = schema.get('name')
        with open("%s/%s.avsc" % (out, name), "w") as f:
            json.dump(schema, f, indent=4)

if __name__ == "__main__":
    segment(SRC, OUT_DIR)
