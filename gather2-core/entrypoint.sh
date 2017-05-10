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
    pip_freeze    : freeze pip dependencies and write to requirements.txt
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

pip_freeze() {
    rm -rf /tmp/env
    virtualenv -p python3 /tmp/env/
    /tmp/env/bin/pip install -f /code/dependencies -r ./primary-requirements.txt --upgrade
    set +x
    echo -e "###\n# frozen requirements DO NOT CHANGE\n# To update this update 'primary-requirements.txt' then run ./entrypoint.sh pip_freeze\n###" | tee requirements.txt
    /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a requirements.txt
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
        coverage run --rcfile="/code/.coveragerc" /code/manage.py test core "${@:2}"
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
        setup_prod_db
        /var/env/bin/python manage.py collectstatic --noinput
        /var/env/bin/uwsgi --ini /code/conf/uwsgi.ini
    ;;
    pip_freeze )
        pip_freeze
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
