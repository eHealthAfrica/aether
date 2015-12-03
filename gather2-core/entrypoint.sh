#!/usr/bin/env bash
set -e
set -x

# Define help message
show_help() {
    echo """
Commands
serve      : Serve the application with uwsgi
manage     : Invoke django manage.py commands
sqlcreate  : Create empty database for Gather2, will still need migrations run
"""
}

case "$1" in
    serve)
        exec uwsgi \
            --master \
            --die-on-term \
            --http-socket 0.0.0.0:8080 \
            --home /code/env/ \
            --processes 4 \
            --module gather2.wsgi \
            --static-map /static=/code/gather2-core/static_root
    ;;
    manage)
        ~/env/bin/python /code/gather2-core/manage.py "${@:2}"
    ;;
    test_coverage)
        ~/env/bin/coverage run --rcfile="/code/.coveragerc" /code/gather2-core/manage.py test core
	mkdir ~/annotated
	~/env/bin/coverage annotate --rcfile="/code/.coveragerc" -d ~/annotated
	cat ~/annotated/*
	~/env/bin/coverage report --rcfile="/code/.coveragerc"
	cat << "EOF"
  ____                 _     _       _     _
 / ___| ___   ___   __| |   (_) ___ | |__ | |
| |  _ / _ \ / _ \ / _` |   | |/ _ \| '_ \| |
| |_| | (_) | (_) | (_| |   | | (_) | |_) |_|
 \____|\___/ \___/ \__,_|  _/ |\___/|_.__/(_)
                          |__/

EOF


    ;;
    sqlcreate )
	~/env/bin/python /code/gather2-core/manage.py sqlcreate | psql -U postgres -h db
    ;;
    *)
        show_help
    ;;
esac
