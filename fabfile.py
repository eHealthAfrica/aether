import os
import zipfile

from fabric.colors import green
from fabric.api import local
from fabconfig import env, prod, stage  # noqa

from jinja2 import Environment, FileSystemLoader

loader = FileSystemLoader('./gather2-core/conf/', followlinks=True)
templateEnv = Environment(loader=loader)


def _get_commit_id():
    return local('git rev-parse HEAD', capture=True)[:20]


def _get_current_branch_name():
    return local('git branch | grep "^*" | cut -d" " -f2', capture=True)


def notify(msg):
    bar = '+' + '-' * (len(msg) + 2) + '+'
    print(green(''))
    print(green(bar))
    print(green("| %s |" % msg))
    print(green(bar))
    print(green(''))


def createDockerrunFile(tag):
    template = templateEnv.get_template('Dockerrun.aws.json.tmpl')
    fname = "gather2-core/conf/Dockerrun.aws.json"
    with open(fname, 'w') as f:
        data = template.render(tag=tag)
        f.write(data)
    notify("Create Dockerrun.aws.json with tag %s" % tag)


def createNginxConfig():
    template = templateEnv.get_template('nginx.gathercore.conf.tmpl')
    fname = "gather2-core/conf/nginx.gathercore.conf"
    with open(fname, 'w') as f:
        data = template.render(subdomain=env.subdomain)
        f.write(data)
    notify("Create nginx.gathercore.conf with hostname: %(hostname)s" % env)


def _zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def createZip():
    zipf = zipfile.ZipFile('gather2-core/conf/deploy.zip', 'w')
    _zipdir('.ebextensions/', zipf)
    zipf.write('gather2-core/conf/Dockerrun.aws.json', arcname='Dockerrun.aws.json')
    zipf.close()


def prebuild():
    createNginxConfig()


def preparedeploy():
    createDockerrunFile(os.environ.get("TRAVIS_TAG", "latest"))
    createZip()
