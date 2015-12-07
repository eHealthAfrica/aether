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
    test )
        cd /code
        python manage.py test
    ;;
    test_coverage )
        coverage run --rcfile="/code/.coveragerc" /code/manage.py test
        mkdir ~/annotated
        coverage annotate --rcfile="/code/.coveragerc" -d ~/annotated
        cat ~/annotated/*
        coverage report --rcfile="/code/.coveragerc"
        cat << "EOF"
  ____                 _     _       _     _
 / ___| ___   ___   __| |   (_) ___ | |__ | |
| |  _ / _ \ / _ \ / _` |   | |/ _ \| '_ \| |
| |_| | (_) | (_) | (_| |   | | (_) | |_) |_|
 \____|\___/ \___/ \__,_|  _/ |\___/|_.__/(_)
                          |__/

EOF


    ;;
    *)
        show_help
    ;;
esac
