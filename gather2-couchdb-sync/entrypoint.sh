#!/bin/bash
set -e
set -x


# Define help message
show_help() {
    echo """
    Commands
    manage        : Invoke django manage.py commands
    setuplocaldb  : Create empty database for gather core
    setupproddb   : Create empty database for production
    test_coverage : runs tests with coverage output
    start         : start webserver behind nginx (prod for serving static files)
    """
}

setup_local_db() {
    set +e
    cd /code/
    /var/env/bin/python manage.py sqlcreate | psql -U $RDS_USERNAME -h $RDS_HOSTNAME
    set -e
    /var/env/bin/python manage.py migrate
}

setup_prod_db() {
    set +e
    cd /code/
    set -e
    export PGPASSWORD=$RDS_PASSWORD
    if psql -h $RDS_HOSTNAME -U $RDS_USERNAME -c "" $RDS_DB_NAME; then
      echo "Database exists!"
    else
      createdb -h $RDS_HOSTNAME -U $RDS_USERNAME -e $RDS_DB_NAME
    fi
    /var/env/bin/python manage.py migrate
}

case "$1" in
    manage )
        cd /code/
        /var/env/bin/python manage.py "${@:2}"
    ;;
    setuplocaldb )
        setup_local_db
    ;;
    setupproddb )
        setup_prod_db
    ;;
    test_coverage)
        source /var/env/bin/activate
        coverage run --rcfile="/code/.coveragerc" /code/manage.py test
        mkdir /var/annotated
        coverage annotate --rcfile="/code/.coveragerc"
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
    start )
        cd /code/
        /var/env/bin/python manage.py collectstatic --noinput
        chmod -R 755 /var/www/static
        /var/env/bin/uwsgi --ini /code/conf/uwsgi.ini
    ;;
    start_rq )
        /var/env/bin/python manage.py rqscheduler &
        /var/env/bin/python manage.py rqworker default
    ;;
    start_rq_dev )
        # In local dev we assign a random name to the rq worker,
        # to get around conflicts when restarting its container.
        # RQ uses the PID as part of it's name and that does not
        # change with container restarts and RQ the exits because
        # it finds the old worker under it's name in redis.
        /var/env/bin/python manage.py rqscheduler &
        /var/env/bin/python manage.py rqworker default --name "rq-${RANDOM}"
    ;;
    bash )
        bash "${@:2}"
    ;;
    help)
        show_help
    ;;
    *)
        show_help
    ;;
esac
