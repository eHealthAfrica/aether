You'll need pipenv installed.

To setup the env run `pipenv --two install`
Whenver you want to work with the tools enter the environment with `pipenv shell`

We specify which Libraries to use, and which schemas to import in salad-bar/conf/settings.json:

{
    "project": "ehaDemo",  # The name of our project
    "$base": "http://demo.eha.org/",  # The base namespace of our project
    "kernel_url": "http://kernel.aether.local:8000/v1",
    "namespaces":{  # Explicit abbreviations for different namespaces (SALAD convention)
        "eha": "http://demo.eha.org/"
    },
    "basetype_name": "BaseModel",  # If all documents needs to inherit from a basemode, we declare that here
    "libraries":{
        "eha.demo.2018.01":{  # The name of the library [Matches name in a library's scrape.json:: salad-bar/library/src/{org}/{library}/scrape.json]
            "schema_file": "2018-01-30-eha.demo.json",  #  Libray file is output to this name in /schemas
            "requirements":[  # The Type names we're requesting from this library
                "http://demo.eha.org/Person",
                "http://demo.eha.org/Child",
                "http://demo.eha.org/Thing"
            ],
            "depth": 3  # The recursion depth from the required schemas where we stop pulling their dependent linked schemas
        }
    }
}

Running:

from inside the pipenv (pipenv shell)
run: python ./wizard.py
Answering Y to all prompts will build the library as configured and register it.


