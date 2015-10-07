from invoke import run, task

import os

os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)

os.environ['PYTHONPATH'] = "{}/src/".format(
    os.path.dirname(os.path.abspath(__file__))
)


@task
def manage(cmd, configuration="Dev"):
    run("bin/python ./src/gather2_core/manage.py {} --configuration {}".format(
        cmd,
        configuration
    ))


@task
def runserver(configuration="Dev"):
    manage("runserver", configuration)


@task
def test(configuration="Test"):
    run("cd src/ && DJANGO_CONFIGURATION={} py.test gather2_core/tests.py".format(
        configuration
    ))


@task
def check():
    run("flake8 --exclude migrations --ignore E501,C901 ./src/gather2_core *.py")


@task
def fix():
    run("autopep8 -r --in-place --exclude migrations --max-line-length 120 ./src/gather2_core *.py")
