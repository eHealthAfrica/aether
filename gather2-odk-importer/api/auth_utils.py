from django.http import HttpResponse


class AuthService(object):

    @staticmethod
    def authorise(username=None, password=None):
        # TODO this is a stubbed method but eventually needs to call into gather
        # core
        return True


class HttpResponseNotAuthorised(HttpResponse):
    status_code = 401

    def __init__(self):
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] =\
            'Basic realm="Gather2-ODK-Importer"'
