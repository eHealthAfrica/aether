#!/bin/bash
set -e


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
    cd /code/gather2-core/
    /var/env/bin/python manage.py sqlcreate | psql -U $RDS_USERNAME -h $RDS_HOSTNAME
    set -e
    /var/env/bin/python manage.py migrate
}

setup_prod_db() {
    set +e
    cd /code/gather2-core/
    set -e
    /var/env/bin/python manage.py migrate
}

setup_logs_forwarding() {
    local logfiles="${*}"
    for logfile in ${logfiles}; do
       cat >> /var/awslogs/etc/awslogs.conf <<EOF
[${logfile}]
file = ${logfile}
log_stream_name = ${PROJECT_NAME}/${logfile}/$(hostname)
initial_position = start_of_file
log_group_name = ${DEPLOY_ENV}
EOF
    done
}

case "$1" in
    manage )
        cd /code/gather2-core/
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
        coverage run --rcfile="/code/.coveragerc" /code/gather2-core/manage.py test core
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
        setup_prod_db
        cd /code/gather2-core/
        /var/env/bin/python manage.py collectstatic --noinput
        /usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf
        setup_logs_forwarding "/var/log/uwsgi/uwsgi.log"
        nginx -g "daemon off;"
    ;;
    bash )
        bash "${@:2}"
    ;;
    *)
        show_help
    ;;
esac
