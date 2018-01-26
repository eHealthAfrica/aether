You'll need pipenv installed. 

To setup the env run `pipenv install`
Whenver you want to work with the tools enter the environment with `pipenv shell`


!#&!#&!#&!#&!#& THIS IS OUTDATED !#&!#&!#&!#&!#&

Setup

1) Turn the schema.org snapshot CSVs into combined json.
    `python ./make_json/make_json.py`

2) Select a few schema.org schemas to require. Add them to the request object in the schema_gen.py method "test_graph"
    For the example to work, you'll need Patient at least.
    request = [
        "http://schema.org/Patient",
        ...
    ]

3) Run schema_gen.py to create limited.json (a subset of the library) & depends.json (a dependency graph)
    `python ./schema_gen.py`

4) In /example, modify or leave extends.json alone.

5) Run schema-salad-tool against extends.json which imports from limited.json.
    `schema-salad-tool ./example.extends.json --print-avro` 

!#&!#&!#&!#&!#& THIS IS OUTDATED !#&!#&!#&!#&!#&
