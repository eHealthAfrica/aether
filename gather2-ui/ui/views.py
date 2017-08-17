import requests
from django.http import HttpResponse
from django.views import View


class ProxyView(View):

    base_url = None
    '''
    The base URL that the proxy should forward requests to.
    '''

    token = None
    '''
    The Authentication Token that the proxy should use to forward requests to ``base_url``.
    '''

    def dispatch(self, request, path, *args, **kwargs):
        self.path = path
        self.original_request_path = request.path
        if not self.path.startswith('/'):
            self.path = '/' + self.path

        # build request path with `base_url` + `path`
        url = u'%s%s' % (self.base_url, self.path)

        request.path = url
        request.path_info = url
        request.META['PATH_INFO'] = url

        if self.token:
            request.META['HTTP_AUTHORIZATION'] = 'Token {token}'.format(token=self.token)

        return super(ProxyView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def post(self, request, data=None, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        def valid_header(name):
            return name.startswith('HTTP_') or name.startswith('CSRF_') or name == 'CONTENT_TYPE'

        headers = {}
        for header, value in request.META.items():
            if valid_header(header):
                norm_header = header.replace('HTTP_', '').title().replace('_', '-')
                headers[norm_header] = value

        param_str = request.GET.urlencode()
        url = request.path + ('?%s' % param_str if param_str else '')

        response = requests.request(method=request.method,
                                    url=url,
                                    data=request.body if request.body else None,
                                    headers=headers,
                                    *args,
                                    **kwargs)

        return HttpResponse(response, status=response.status_code)
