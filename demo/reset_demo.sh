#!/bin/bash

echo "Killing ES index for aether-demo-2"
curl -X DELETE "http://localhost:9200/aether-demo-2"
echo "\nrecreating ES index aether-demo-2"
`curl -X PUT "http://localhost:9200/aether-demo-2" -H 'Content-Type: application/json' -d '
{
    "mappings": {
        "location": {
	        "properties": {
		        "location": {
			        "type": "geo_point"
		        }
	        }
        },
        "household": {
            "_parent": {
		        "type": "location"
	        }
        },
        "person": {
	        "_parent": {
		        "type": "household"
	        }
        }
    }
}'`

echo "Setting up Project Data"

pipenv --three --where install
pipenv run python ./setup_project.py

echo "You may now submit data to the server"
