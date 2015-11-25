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
            --home /opt/env/ \
            --processes 4 \
            --module gather2.wsgi \
            --static-map /static=/opt/gather2-core/static_root
    ;;
    manage)
        /opt/gather2-core/manage.py "${@:2}"
    ;;
    test_coverage)
        ~/env/bin/coverage run --rcfile="/opt/.coveragerc" /opt/gather2-core/manage.py test core.tests.SimpleTestCase.test_query_decorator
	mkdir ~/annotated
	~/env/bin/coverage annotate --rcfile="/opt/.coveragerc" -d ~/annotated
	cat ~/annotated/*
	~/env/bin/coverage report --rcfile="/opt/.coveragerc"

    ;;
    sqlcreate )
	~/env/bin/python /opt/gather2-core/manage.py sqlcreate | psql -U postgres -h localhost
    ;;
    *)
        show_help
    ;;
esac
