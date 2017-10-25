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

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    build         : build package module
    """
}

test_flake8() {
    flake8 /code/. --config=/code/conf/extras/flake8.cfg
}

test_coverage() {
    export RCFILE=/code/conf/extras/coverage.rc
    export TESTING=true
    export DEBUG=false

    coverage run    --rcfile="$RCFILE" manage.py test "${@:1}"
    coverage report --rcfile="$RCFILE"
    coverage erase
    rm -rf /code/.hypothesis

    cat /code/conf/extras/good_job.txt
}

# --------------------------------
# set DJANGO_SECRET_KEY if needed
if [ "$DJANGO_SECRET_KEY" = "" ]
then
   export DJANGO_SECRET_KEY=$(
        cat /dev/urandom | tr -dc 'a-zA-Z0-9-_!@#$%^&*()_+{}|:<>?=' | fold -w 64 | head -n 4
    )
fi
# --------------------------------


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
        pip install -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
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
        # test before building
        test_flake8
        test_coverage

        # remove previous build if needed
        rm -rf dist
        rm -rf build
        rm -rf gather2.common.egg-info

        # create the distribution
        python setup.py bdist_wheel

        # remove useless content
        rm -rf build
        rm -rf gather2.common.egg-info
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
