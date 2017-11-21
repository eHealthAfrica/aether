import requests

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.views import View

from .models import get_or_create_valid_app_token, AETHER_APPS


def tokens_required(function=None, redirect_field_name=None, login_url='tokens'):
    '''
    Decorator for views that checks that a user is logged in and
    he/she has valid tokens for each app used in the proxy view,
    redirecting to the "tokens" endpoint if erred.
    '''

    def user_token_test(user):
        '''
        Checks for each external app that the user can currently connect to it.
        '''
        try:
            for app in AETHER_APPS:
                # checks if there is a valid token for this app
                if get_or_create_valid_app_token(user, app) is None:
                    return False
            return True
        except Exception:
            return False

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and user_token_test(u),
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:  # pragma: no cover
        return actual_decorator(function)
    return actual_decorator  # pragma: no cover


class TokenProxyView(View):
    '''
    This view will proxy any request to the indicated app with the user auth token.
    '''

    app_name = None
    '''
    The app that the proxy should forward requests to.
    '''

    def dispatch(self, request, path, *args, **kwargs):
        '''
        Dispatches the request including/modifying the needed properties
        '''

        if self.app_name not in AETHER_APPS:
            raise RuntimeError('"{}" app is not recognized.'.format(self.app_name))

        app_token = get_or_create_valid_app_token(request.user, self.app_name)
        if app_token is None:
            raise RuntimeError('User "{}" cannot conenct to app "{}"'
                               .format(request.user, self.app_name))

        self.path = path
        self.original_request_path = request.path
        if not self.path.startswith('/'):
            self.path = '/' + self.path

        # build request path with `base_url` + `path`
        url = '{base_url}{path}'.format(base_url=app_token.base_url, path=self.path)

        request.path = url
        request.path_info = url
        request.META['PATH_INFO'] = url
        request.META['HTTP_AUTHORIZATION'] = 'Token {token}'.format(token=app_token.token)

        return super(TokenProxyView, self).dispatch(request, *args, **kwargs)

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

    def post(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        def valid_header(name):
            '''
            Validates if the header can be passed within the request headers.
            '''
            return (
                name.startswith('HTTP_') or
                name.startswith('CSRF_') or
                name == 'CONTENT_TYPE'
            )

        method = request.method
        # builds request headers
        headers = {}
        for header, value in request.META.items():
            # Fixes:
            # django.http.request.RawPostDataException:
            #     You cannot access body after reading from request's data stream
            #
            # Django does not read twice the `request.body` on `POST` calls:
            # but it was already read while checking the CSRF token.
            # This raises an exception in the line below `data=request.body ...`.
            # The Ajax call changed it from `POST` to `PUT`,
            # here it's changed back to its real value.
            #
            # All the conditions are checked to avoid further issues with this.
            if method == 'PUT' and header == 'HTTP_X_METHOD' and value == 'POST':
                method = value

            if valid_header(header):
                # normalize header name
                norm_header = header.replace('HTTP_', '').title().replace('_', '-')
                headers[norm_header] = value

        # builds url with the query string
        param_str = request.GET.urlencode()
        url = request.path + ('?{}'.format(param_str) if param_str else '')

        response = requests.request(method=method,
                                    url=url,
                                    data=request.body if request.body else None,
                                    headers=headers,
                                    *args,
                                    **kwargs)
        return HttpResponse(response, status=response.status_code)
