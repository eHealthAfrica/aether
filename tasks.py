from invoke import run, task

import os
os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)

@task
def runserver(configuration="Dev"):
    run("bin/python ./src/gather2_core/manage.py runserver --configuration {}".format(
      configuration
    ))

@task
def test(configuration="Test"):
    run("cd src/ && DJANGO_CONFIGURATION={} py.test gather2_core/tests.py".format(
        configuration
    ))

@task
def check():
    run("flake8 --exclude migrations --ignore E501,C901 ./src/gather2_core")

@task
def fix():
    run("autopep8 -r --in-place --exclude migrations --max-line-length 120 ./src/gather2_core")
