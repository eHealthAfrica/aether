#!/bin/bash

# This script registers connectors in Kafka.  Each connector to register should have 
# it's own properties file in Kafka JSON format. A delay can be passed in in order to give
# Kafka time to initialize and it will retry several times if it gets a connection refused
# response from the Kafka server.
#
# Passed parameters:
# $1 : Delay, formatted for the sleep command.  '0' = no delay
# $2 : Connection file to push to Kafka.  If unset, then all JSON files in the 
# /aether folder will be registered
#

# If a delay time came in, then delay
if [ "$1" != "" ] && [ "$1" != "0" ]; then
    echo "...Delay before Adding Kafka Connections : " $1
    sleep $1
fi

# If no files were passed in, grab all .json files and submit them
FILE="/aether/*.json"
if [ "$2" != "" ]; then
  FILE=$2
fi

for f in $FILE
do
    echo "...Adding Kafka Connection - " $f
    i=4
    until [ $i -le 0 ]
    do
    	((i--))
	    curl -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d @$f http://kafka:8083/connectors
	    # exit code of 7 from curl is 'Connection refused' which means it's not running yet
	    if [ $? -eq 7 ] && [ $i -gt 0 ]; then
	        echo "Waiting 30 sec then retry -" $i
	        sleep 30
	    else
            echo "...Successfully added - " $f
	        i=0
	    fi
    done
done