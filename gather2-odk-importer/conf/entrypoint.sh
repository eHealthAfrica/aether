#!/bin/bash
set -e


# Define help message
show_help() {
    echo """
    Commands
    manage     : Invoke django manage.py commands
    setupdb  : Create empty database, will still need migrations run
    """
}

source ~/env/bin/activate
cd /code/

case "$1" in
    manage)
        python manage.py "${@:2}"
    ;;
    setupdb )
        python manage.py sqlcreate | psql -U postgres -h db
        python manage.py migrate
    ;;
    test )
        python manage.py test
    ;;
    test_coverage )
        coverage run --rcfile="/code/.coveragerc" /code/manage.py test
        mkdir ~/annotated
        coverage annotate --rcfile="/code/.coveragerc" -d ~/annotated
        coverage report --rcfile="/code/.coveragerc" || cat ~/annotated/*
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
