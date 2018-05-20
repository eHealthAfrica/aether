import requests

from django.http import HttpResponse
from rest_framework.response import Response
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action

from ..settings import AETHER_APPS
from . import models, serializers, utils as ui_utils


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = models.Pipeline.objects.all()
    serializer_class = serializers.PipelineSerializer
    ordering = ('name',)

    @action(methods=['post'], detail=False)
    def fetch(self, request):
        '''
        This view gets kernel objects, transforms and loads into a pipeline
        '''
        ui_utils.kernel_to_pipeline()
        pipelines = models.Pipeline.objects.all()
        serialized_data = serializers.PipelineSerializer(pipelines, context={'request': request}, many=True).data
        return Response(serialized_data, status=200)

    @action(methods=['post'], detail=True)
    def publish(self, request, pk=None):
        '''
        This view transform the supplied pipeline to kernal models,
        publish and update the pipeline with related kernel model ids.
        '''
        project_name = request.data['project_name'] if 'project_name' in request.data else 'Aux'
        outcome = {
            'successful': [],
            'error': [],
            'exists': []
        }
        try:
            pipeline = get_object_or_404(models.Pipeline, pk=pk)
        except Exception as e:
            outcome['error'].append(str(e))
            return Response(outcome, status=400)
        outcome = ui_utils.publish_preflight(pipeline, project_name, outcome)
        if len(outcome['error']) or len(outcome['exists']):
            return Response(outcome, status=400)
        else:
            outcome = ui_utils.publish_pipeline(pipeline, project_name)
            if len(outcome['error']):
                return Response(outcome, status=400)
            else:
                del outcome['error']
                return Response(outcome, status=200)


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

        app_token = models.UserTokens.get_or_create_user_app_token(request.user, self.app_name)
        if app_token is None:
            raise RuntimeError('User "{}" cannot connect to app "{}"'
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

                # nginx also checks HTTP-X-FORWARDED-... headers
                # if not present it changed back to something similar to:
                #    original request:
                #           {https-ui-server}/{app}/{path}?{querystring}
                #    transformed request by this view:
                #           {https-app-server}/{path}?{querystring}
                #    what nginx does afterward:
                #           https://{https-app-server}/{path}?{querystring}
                #    or
                #           {https-ui-server}/{path}?{querystring}
                # obviously, all of them fail and this only happens
                # on the servers with nginx, not locally :(
                if header.startswith('HTTP_X_FORWARDED_'):  # pragma: no cover
                    norm_header = header.title().replace('_', '-')
                    headers[norm_header] = value

        # bugfix: We need to remove the Host from the header
        # since the request goes to another host, otherwise
        # the webserver returns a 404 because the domain is
        # not hosted on that server. The webserver
        # should add the correct Host based on the request.
        # this problem might not be exposed running on localhost

        if 'Host' in headers:  # pragma: no cover
            del headers['Host']

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
