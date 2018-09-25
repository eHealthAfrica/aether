import bravado
import bravado_core
from bravado.client import SwaggerClient, ResourceDecorator, CallableOperation
from bravado.config import BravadoConfig
from bravado_core.spec import Spec
from bravado.requests_client import RequestsClient
from bravado.swagger_model import Loader
import json
from requests.auth import HTTPBasicAuth

import logging

log = logging.getLogger(__name__)

# An Exception Class to wrap all handled API exceptions


class AetherAPIException(Exception):
    def __init__(self, *args, **kwargs):
        msg = {k: v for k, v in kwargs.items()}
        print(kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(msg)


class Client(SwaggerClient):

    def __init__(self, url, user, pw, log_level=logging.ERROR):
        log.setLevel(log_level)
        spec_url = '%s/v1/schema/?format=openapi' % url
        http_client = RequestsClient()
        domain = url.split('://')[1]
        http_client.set_basic_auth(domain, user, pw)
        loader = Loader(http_client, request_headers=None)
        try:
            spec_dict = loader.load_spec(spec_url)
        except bravado.exception.HTTPForbidden as forb:
            log.error('Could not authenticate with provided credentials')
            raise forb
        except bravado.exception.HTTPBadGateway as bgwe:
            log.error('Server Unavailable')
            raise bgwe
        # Our Swagger spec is apparently somewhat invalid.
        config = {
            'validate_swagger_spec': False,
            'validate_responses': False
        }
        # We take this from the from_url class method of SwaggerClient
        # Apply bravado config defaults
        bravado_config = BravadoConfig.from_config_dict(config)
        # remove bravado configs from config dict
        for key in set(bravado_config._fields).intersection(set(config)):
            del config[key]
        # set bravado config object
        config['bravado'] = bravado_config
        swagger_spec = Spec.from_dict(
            spec_dict, spec_url, http_client, config)
        self.__also_return_response = True
        self.swagger_spec = swagger_spec
        super(Client, self).__init__(
            swagger_spec, also_return_response=self.__also_return_response)

    def _get_resource(self, item):
        # We override this method to use our AetherDecorator class
        resource = self.swagger_spec.resources.get(item)
        if not resource:
            raise AttributeError(
                'Resource {0} not found. Available resources: {1}'
                .format(item, ', '.join(dir(self))))

        # Wrap bravado-core's Resource and Operation objects in order to
        # execute a service call via the http_client.
        # Replaces with AetherSpecific handler
        return AetherDecorator(resource, self.__also_return_response)

    def __getitem__(self, name):
        return getattr(self, name)


class AetherDecorator(ResourceDecorator):

    def __init__(self, resource, also_return_response=True):
        self.name = resource.name
        self.handled_exceptions = [
            bravado.exception.HTTPBadRequest,
            bravado.exception.HTTPBadGateway,
            bravado.exception.HTTPNotFound
        ]
        super(AetherDecorator, self).__init__(
            resource, also_return_response)

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        fn = CallableOperation(
            getattr(self.resource, self._get_full_name(name)),
            self.also_return_response)
        # It was annoying to constantly call .response().result to get to the most
        # valuable data. Also errors were being swallowed by the inner workings of
        # Bravado. Wrapping the returned function handles this.

        def resultant_function(*args, **kwargs):
            # try:
            future = fn(*args, **kwargs)
            # We just want to give the exception right back, but maintain
            # access to the response object so that we can grab the error.
            # When the exception is caught and handled normally, this is impossible.
            # Hence the lambda
            response = future.response(
                fallback_result=lambda x: x,
                exceptions_to_catch=tuple(self.handled_exceptions)
            )
            result = response.result
            if any([isinstance(result, i) for i in self.handled_exceptions]):
                http_response = response.incoming_response
                assert isinstance(http_response, bravado_core.response.IncomingResponse)
                details = {
                    'operation': future.operation.operation_id,
                    'status_code': http_response.status_code,
                }
                try:
                    details['response'] = http_response.json()['name']
                except KeyError as err:
                    details['response'] = str(result)
                raise AetherAPIException(**details)
            return result

        return resultant_function

    def _get_full_name(self, name):
        return "%s_%s" % (self.name, name)

    def _verify_param(self, name, param_name):
        operation = getattr(self.resource, self._get_full_name(name))
        if not param_name in operation.params:
            raise ValueError("%s has no parameter %s" % (name, param_name))
        return True

    def _verify_params(self, name, params):
        return all([self._verify_param(name, i) for i in params])

    def __iter__(self):
        # show available rpc calls
        return iter([i.lstrip("%s_" % self.name) for i in self.__dir__()])

    def paginated(self, remote_function, start_page=1, ordering='modified', **kwargs):
        fn = getattr(self, remote_function)
        params = dict(kwargs)
        self._verify_params(remote_function, params.keys())
        page = start_page
        params['page'] = page
        params['ordering'] = ordering
        _next = True
        while _next:
            params['page'] = page
            result = fn(**params)
            _next = result.get('next')
            page += 1
            results = result.get('results')
            if not results:
                raise StopIteration
            for item in results:
                yield(item)

    def count(self, remote_function, **kwargs):
        fn = getattr(self, remote_function)
        params = dict(kwargs)
        self._verify_params(remote_function, params.keys())
        result = fn(**params)
        return result.get('count')

    def first(self, remote_function, **kwargs):
        fn = getattr(self, remote_function)
        params = dict(kwargs)
        self._verify_params(remote_function, params.keys())
        result = fn(**params)
        return result.get('results', [])[0]
