#!/bin/bash
set -e


# Define help message
show_help() {
    echo """
    Commands
    manage     : Invoke django manage.py commands
    setupdb  : Create empty database for Gather2, will still need migrations run
    """
}

case "$1" in
    manage)
        cd /code
        python manage.py "${@:2}"
    ;;
    setupdb )
        cd /code
        psql -U postgres -h db -c "create database odkimporter"
        python manage.py syncdb
        python manage.py migrate
    ;;
    *)
        show_help
    ;;
esac
