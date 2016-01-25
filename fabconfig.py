from fabric.api import env

env.project_code = "gather2-core"
env.require_tag = True


def _configure(build_name):
    env.build_name = build_name
    env.nginx_file_path = "gather2-core/conf/nginx.gathercore.conf"
    env.supervisor_file_path = "gather2-core/conf/supervisor.gathercore.conf"
    env.subdomain = "%(project_code)s-%(build_name)s" % env
    env.hostname = "%(subdomain)s.elasticbeanstalk.com" % env


def stage():
    _configure("stage")


def prod():
    _configure("prod")
