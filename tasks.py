from invoke import run, task

import os
os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)

@task
def runserver(configuration="Dev"):
    run("bin/python ./gather2-core/manage.py runserver --configuration {}".format(
      configuration
    ))

@task
def test(configuration="Test"):
    run("cd gather2-core && DJANGO_CONFIGURATION={} py.test core/tests.py".format(
        configuration
    ))

@task
def check():
    run("flake8 --exclude migrations --ignore E501,C901 ./gather2-core")

@task
def fix():
    run("autopep8 -r --in-place --exclude migrations --max-line-length 120 ./gather2-core")
