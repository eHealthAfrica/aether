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
    setuplocaldb  : create/migrate database for development (creates superuser and token)

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    start         : start webserver behind nginx
    start_dev     : start webserver for development
    """
}

test_flake8() {
    flake8 /code/. --config=/code/setup.cfg
}

test_coverage() {
    # Python2 Tests !!Must run first as we rely on the schema generation
    python2 setup.py -q test "${@:1}"

    cat /code/conf/extras/good_job.txt

    # Python3 Tests
    python3 setup.py test "${@:1}"

    cat /code/conf/extras/good_job.txt
    rm -R ./*.egg*
    rm -R .pytest_cache
}


case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    manage )
        ./manage.py "${@:2}"
    ;;

    pip_freeze )
        rm -rf /tmp/env
        pip2 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.py2.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.py2.txt
        pip2 freeze --local | grep -v appdir | tee -a conf/pip/requirements.py2.txt

        rm -rf /tmp/env
        pip3 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.py3.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.py3.txt
        pip3 freeze --local | grep -v appdir | tee -a conf/pip/requirements.py3.txt
    ;;

    setuplocaldb )
        #setup_db
        #setup_initial_data
    ;;

    setupproddb )
        setup_db
    ;;

    test)
        test_flake8
        test_coverage "${@:2}"
    ;;

    test_lint)
        test_flake8
    ;;

    test_coverage)
        test_coverage "${@:2}"
    ;;

    build)
        # remove previous build if needed
        rm -rf dist
        rm -rf build
        rm -rf aether.client.egg-info

        # create the distribution
        python setup.py bdist_wheel --universal

        # remove useless content
        rm -rf build
        rm -rf aether.client.egg-info
    ;;

    start )
        echo 'start'
    ;;

    start_dev )
        echo 'start_dev'
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
