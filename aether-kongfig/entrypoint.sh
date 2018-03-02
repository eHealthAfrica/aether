#!/bin/bash

SEARCH_TEXT=${SEARCH_TEXT:-kong}

ARGUMENTS=( "$@" )
while :
do
    case "$1" in
        --path )
            CONFIG_FILE=$2
            shift 2
            ;;
        --host )
            HOST=$2
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

if [ -n "$CONFIG" ]; then
    echo "Writing $CONFIG_FILE from the \$CONFIG environment variable"
    echo "$CONFIG" > "$CONFIG_FILE"

    if [ "true" == "$DEBUG" ]; then
        cat "$CONFIG_FILE"
    fi
fi

COUNTER=0
echo -n "waiting for $HOST to start up..."
trap 'exit' INT
while [  $COUNTER -lt ${CHECK_ATTEMPTS} ]; do
    let COUNTER=COUNTER+1
    if `curl -s $HOST | grep -q -i "$SEARCH_TEXT"`; then
        echo "started"
        sleep ${POST_START_DELAY}
        kongfig "${ARGUMENTS[@]}"
        exit $?
    else
        echo -n "."
    fi
    sleep ${BETWEEN_CHECK_DELAY}
done
