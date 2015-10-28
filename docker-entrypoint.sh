#!/usr/bin/env bash
set -e

# Define help message
show_help() {
    echo """
Usage: docker run <imagename> COMMAND
Commands
serve      : Serve the application with uwsgi
manage     : Invoke django manage.py commands
"""
}

case "$1" in
    serve)
        exec uwsgi \
            --master \
            --die-on-term \
            --http-socket 0.0.0.0:8080 \
            --home /opt/gather2/venv/ \
            --processes 4 \
            --module gather2_core.wsgi \
            --static-map /static=/var/www/data \
    ;;
    manage)
        /opt/gather2/venv/bin/python /opt/gather2/venv/lib/python3.4/site-packages/gather2_core/manage.py "${@:2}"
    ;;
    *)
        show_help
    ;;
esac
