import json


from os.path import abspath
from schema_salad import schema, validate, jsonld_context
from schema_salad.ref_resolver import Loader, file_uri

def pprint(obj):
    print(json.dumps(obj, indent=2))


class SaladHandler(object):

    def __init__(self, path, strict=True):
        self.load_salad(path, strict)

    def load_salad(self, path, strict=True):
        with open(path) as f:
            pass

        metaschema_names, metaschema_doc, metaschema_loader = schema.get_metaschema()
        schema_uri = file_uri(abspath(path))
        schema_raw_doc = metaschema_loader.fetch(schema_uri)

        try: # parse the schema
            schema_doc, schema_metadata = metaschema_loader.resolve_all(
                    schema_raw_doc, schema_uri)
        except (validate.ValidationException) as vale:
            print("Error loading schema %s" % vale)
            raise vale



        # Get the json-ld context and RDFS representation from the schema
        metactx = {}  # type: Dict[str, str]
        if isinstance(schema_raw_doc, dict):
            metactx = schema_raw_doc.get("$namespaces", {})
            if "$base" in schema_raw_doc:
                metactx["@base"] = schema_raw_doc["$base"]
        if schema_doc is not None:
            (schema_ctx, rdfs) = jsonld_context.salad_to_jsonld_context(
                schema_doc, metactx)
        else:
            raise Exception("schema_doc is None??")

        # Create the loader that will be used to load the target document.
        document_loader = Loader(schema_ctx)

        try:

            schema.validate_doc(metaschema_names, schema_doc,
                                metaschema_loader, strict,
                                source=schema_metadata.get("name"))

        except (validate.ValidationException) as vale:
            print("Error validating schema %s" % vale)
            raise vale

        self.schema_doc = schema_doc
        self.document_loader = document_loader
        self.schema_ctx = schema_ctx
        print("Salad schema is valid and loaded")



if __name__ == "__main__":
    handler = SaladHandler("./extends.json")



