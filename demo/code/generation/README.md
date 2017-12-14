#instructions

requires python3 and FRESH running aether instance with default configuration
Any other config requires changes to URLS and AUTH settings in the scripts

install pipenv with: 
    sudo pip3 install pipenv

use pipenv to install dependencies in folder with script    
    pipenv install pyyaml avro-python3 requests

set value for # of entities to generate in script (CREATION_MAX)

run generate.py within pipenv environment
    #setup the project
    pipenv run python3 setup_project.py
    #create a bunch of entities
    pipenv run python3 generate.py

To recreate yor project setup, delete gen_cache.json and run setup_project again.
