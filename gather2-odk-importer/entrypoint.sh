#!/bin/bash
set -e


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command
    manage        : invoke django manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    setupproddb   : create/migrate database for production
    setuplocaldb  : create/migrate database for development (creates superuser)

    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    start         : start webserver behind nginx
    start_dev     : start webserver for development
    """
}

setup_db() {
    export PGPASSWORD=$RDS_PASSWORD
    export PGHOST=$RDS_HOSTNAME
    export PGUSER=$RDS_USERNAME

    until pg_isready -q; do
      >&2 echo "Waiting for postgres..."
      sleep 1
    done

    if psql -c "" $RDS_DB_NAME; then
      echo "$RDS_DB_NAME database exists!"
    else
      createdb -e $RDS_DB_NAME
      echo "$RDS_DB_NAME database created!"
    fi

    # migrate data model if needed
    /var/env/bin/python manage.py migrate --noinput
}

setup_initial_data() {
    # create initial superuser
    /var/env/bin/python manage.py loaddata /code/conf/extras/users_initial.json
}


case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    manage )
        /var/env/bin/python manage.py "${@:2}"
    ;;

    pip_freeze )
        rm -rf /tmp/env
        virtualenv -p python3 /tmp/env/
        /tmp/env/bin/pip install -f /code/dependencies -r ./primary-requirements.txt --upgrade

        cat /code/conf/extras/requirements_header.txt | tee requirements.txt
        /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a requirements.txt
    ;;

    setuplocaldb )
        setup_db
        setup_initial_data
    ;;

    setupproddb )
        setup_db
    ;;

    test_lint)
        /var/env/bin/python -m flake8 /code/. --config=/code/conf/extras/flake8.cfg
    ;;

    test_coverage)
        source /var/env/bin/activate
        export RCFILE=/code/conf/extras/coverage.rc

        coverage erase
        coverage run      --rcfile="$RCFILE" /code/manage.py test "${@:2}"
        coverage report   --rcfile="$RCFILE"

        cat /code/conf/extras/good_job.txt
    ;;

    start )
        setup_db

        /var/env/bin/python manage.py collectstatic --noinput
        chmod -R 755 /var/www/static
        /var/env/bin/uwsgi --ini /code/conf/uwsgi.ini
    ;;

    start_dev )
        setup_db
        setup_initial_data

        /var/env/bin/python manage.py runserver 0.0.0.0:$WEB_SERVER_PORT
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
