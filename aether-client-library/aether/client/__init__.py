# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
from time import sleep

import bravado
import bravado_core

from bravado.client import SwaggerClient, ResourceDecorator, CallableOperation, construct_request
from bravado.config import bravado_config_from_config_dict
from bravado.requests_client import RequestsClient
from bravado.swagger_model import Loader

LOG = logging.getLogger(__name__)


# An Exception Class to wrap all handled API exceptions
class AetherAPIException(Exception):
    def __init__(self, *args, **kwargs):
        msg = {k: v for k, v in kwargs.items()}
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(AetherAPIException, self).__init__(msg)


class Client(SwaggerClient):

    def __init__(self, url, user, pw, log_level=logging.ERROR, config=None, domain=None):
        LOG.setLevel(log_level)
        # Our Swagger spec is apparently somewhat problematic, so we default to no validation.
        config = config or {
            'validate_swagger_spec': False,
            'validate_requests': False,
            'validate_responses': False
        }
        domain = domain or url.split('://')[1].split(':')[0]  # TODO Use Regex
        spec_url = '%s/v1/schema/?format=openapi' % url

        http_client = RequestsClient()
        http_client.set_basic_auth(domain, user, pw)
        loader = Loader(http_client, request_headers=None)
        try:
            spec_dict = loader.load_spec(spec_url)
        except bravado.exception.HTTPForbidden as forb:
            LOG.error('Could not authenticate with provided credentials')
            raise forb
        except (
            bravado.exception.HTTPBadGateway,
            bravado.exception.BravadoConnectionError
        ) as bgwe:
            LOG.error('Server Unavailable')
            raise bgwe

        # We take this from the from_url class method of SwaggerClient
        # Apply bravado config defaults
        bravado_config = bravado_config_from_config_dict(config)
        # remove bravado configs from config dict
        for key in set(bravado_config._fields).intersection(set(config)):
            del config[key]
        # set bravado config object
        config['bravado'] = bravado_config
        swagger_spec = bravado_core.spec.Spec.from_dict(
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
        return AetherDecorator(resource, self.__also_return_response, self.swagger_spec)

    def __getitem__(self, name):
        return getattr(self, name)


# useful for debugging issues with outgoing requests. Only called when ll == DEBUG
def show_request(operation, *args, **kwargs):
    request_options = kwargs.pop('_request_options', {})
    request_params = construct_request(
        operation, request_options, **kwargs)
    return([kwargs, request_params])


'''
Some arguments don't properly display in the swagger specification so we have
to add them at runtime for the client to support them. This includes all payload
filters like payload__name=John. Normally payload__name wouldn't be found in the
spec and an error would be produced.
'''


def mockParam(name, op, swagger_spec):
    param_spec = {'name': name, 'in': 'query',
                  'description': "", 'required': False, 'type': 'string'}
    return bravado_core.param.Param(swagger_spec, op, param_spec)


class AetherDecorator(ResourceDecorator):

    def __init__(self, resource, also_return_response=True, swagger_spec=None):
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
        # Errors in connection worthy of a retry
        self.retry_exceptions = [
            bravado.exception.BravadoTimeoutError,
            bravado.exception.BravadoConnectionError
        ]
        self.swagger_spec = swagger_spec
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
            LOG.debug(show_request(
                getattr(self.resource, self._get_full_name(name)),
                *args,
                **kwargs
            ))
            # This is an attempt to fix an error that only occurs in travis where kernel
            # connections are dropped in transit or by kernel.
            dropped_retries = 5
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
                except tuple(self.retry_exceptions) as err:
                    LOG.debug("error %s in connection to client" % (err))
                    if x == dropped_retries - 1:
                        LOG.error('failed after %s connections to %s' %
                                  (x, future.operation.operation_id))
                        raise err
                    LOG.debug('dropped connection %s to %s, retry' %
                              (x, future.operation.operation_id))
                    sleep(.25 + (.25 * x))
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
                except Exception:
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
        # allow searching for arbitrary fields within the payload
        if param_name.startswith('payload__'):
            # add it to the allowed list of parameters
            operation.params[param_name] = mockParam(param_name, operation, self.swagger_spec)
            return True
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
            # if not results:  # WARNING: this is true with empty lists []
            if results is None:
                raise StopIteration
            for item in results:
                yield item

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
