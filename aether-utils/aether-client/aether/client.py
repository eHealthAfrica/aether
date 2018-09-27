import bravado
import bravado_core
from bravado.client import SwaggerClient, ResourceDecorator, CallableOperation, construct_request
from bravado.config import BravadoConfig
from bravado_core.spec import Spec
from bravado.requests_client import RequestsClient
from bravado.swagger_model import Loader
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep

log = logging.getLogger(__name__)


# An Exception Class to wrap all handled API exceptions
class AetherAPIException(Exception):
    def __init__(self, *args, **kwargs):
        msg = {k: v for k, v in kwargs.items()}
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(msg)


class RetrySession(requests.Session):

    def __init__(self,
                 retries=3,
                 backoff_factor=0.2,
                 status_forcelist=(104, 500, 502)):

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            status=retries,
            method_whitelist=Retry.DEFAULT_METHOD_WHITELIST,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        super(RetrySession, self).__init__()
        self.mount('http://', adapter)
        self.mount('https://', adapter)


class Client(SwaggerClient):

    def __init__(self, url, user, pw, log_level=logging.ERROR, config=None, domain=None):
        log.setLevel(log_level)
        # Our Swagger spec is apparently somewhat problematic, so we default to no validation.
        config = config or {
            'validate_swagger_spec': False,
            'validate_requests': False,
            'validate_responses': False
        }
        domain = domain or url.split('://')[1].split(':')[0]  # TODO Use Regex
        spec_url = '%s/v1/schema/?format=openapi' % url

        http_client = RequestsClient()
        http_client.session = RetrySession()  # User a more complex failure strategy
        http_client.set_basic_auth(domain, user, pw)
        loader = Loader(http_client, request_headers=None)
        try:
            spec_dict = loader.load_spec(spec_url)
        except bravado.exception.HTTPForbidden as forb:
            log.error('Could not authenticate with provided credentials')
            raise forb
        except (
            bravado.exception.HTTPBadGateway,
            bravado.exception.BravadoConnectionError
        ) as bgwe:
            log.error('Server Unavailable')
            raise bgwe

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


# useful for debugging issues with outgoing requests. Only called when ll == DEBUG
def show_request(operation, *args, **kwargs):
    request_options = kwargs.pop('_request_options', {})
    request_params = construct_request(
        operation, request_options, **kwargs)
    return([kwargs, request_params])


class AetherDecorator(ResourceDecorator):

    def __init__(self, resource, also_return_response=True):
        self.name = resource.name
        # The only way to be able to form coherent exceptions is to catch these
        # common types and wrap them in our own, exposing the status and error
        # feeback from the API.
        self.handled_exceptions = [
            bravado.exception.HTTPBadRequest,
            bravado.exception.HTTPBadGateway,
            bravado.exception.HTTPNotFound,
            bravado.exception.HTTPForbidden
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
            # On debug, show outgoing requests
            log.debug(show_request(
                getattr(self.resource, self._get_full_name(name)),
                *args,
                **kwargs
            ))
            # This is an attempt to fix an error that only occurs in travis where kernel
            # connections are dropped.
            for x in range(dropped_retries):
                try:
                    # We just want to give the exception right back, but maintain
                    # access to the response object so that we can grab the error.
                    # When the exception is caught and handled normally, this is impossible.
                    # Hence the lambda returning the exception itself when an exception occurs.
                    response = future.response(
                        timeout=1,
                        fallback_result=lambda x: x,
                        exceptions_to_catch=tuple(self.handled_exceptions)
                    )
                    break
                except bravado.exception.BravadoConnectionError as err:
                    if x == dropped_retries - 1:
                        log.error('failed connection to %s' % future.operation_id)
                        raise err
                    log.error('dropped connection to %s, retry' % future.operation_id)
                    sleep(.25)
            result = response.result
            # If the result is an exception, we expose it's parts along with
            # content from the request response and raise it
            if any([isinstance(result, i) for i in self.handled_exceptions]):
                details = {
                    'operation': future.operation.operation_id,
                    'response': str(result)
                }
                http_response = response.incoming_response
                assert isinstance(http_response, bravado_core.response.IncomingResponse)
                details['status_code'] = http_response.status_code
                try:
                    details['response'] = http_response.json()
                except Exception as err:
                    # JSON is unavailable, so we just use the original exception text.
                    pass
                raise AetherAPIException(**details)
            return result
        return resultant_function

    def _get_full_name(self, name):
        # Allows us to use for example 'entities.create' instead of 'entities.entities_create'
        return "%s_%s" % (self.name, name)

    def _verify_param(self, name, param_name):
        operation = getattr(self.resource, self._get_full_name(name))
        if param_name not in operation.params:
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
