# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.utils.translation import ugettext as _

from django_eha_sdk.health.utils import (
    check_external_app,
    get_external_app_url,
    get_external_app_token,
)
from django_eha_sdk.utils import request
from django_eha_sdk.multitenancy.utils import add_instance_realm_in_headers

from ..errors import KernelPropagationError


# list of messages that can be translated
MSG_KERNEL_CONNECTION_ERR = _(
    'Connection with Aether Kernel server is not possible.'
)
MSG_KERNEL_RESPONSE_ERR = _(
    'Unexpected response from Aether Kernel server '
    'while trying to create/update the project artefacts "{project_id}".\n'
    'Response: {content}'
)

EXTERNAL_APP_KERNEL = 'aether-kernel'


def check_kernel_connection():
    return check_external_app(EXTERNAL_APP_KERNEL)


def get_kernel_url():
    return get_external_app_url(EXTERNAL_APP_KERNEL)


def get_kernel_auth_header():
    return {'Authorization': f'Token {get_external_app_token(EXTERNAL_APP_KERNEL)}'}


def propagate_kernel_project(project, family=None):
    '''
    Creates a copy of the indicated project in Aether Kernel
    and creates/updates its linked artefacts based on the given AVRO schemas.

    One AVRO schema should create/update in Kernel:
        - one Project,
        - one Mapping,
        - one Schema and
        - one Schema Decorator.
    '''

    artefacts = {
        'name': project.name,
        'family': family,
        'avro_schemas': [],
    }

    for schema in project.schemas.order_by('name'):
        artefacts['avro_schemas'].append(__parse_schema(schema))

    __upsert_kernel_artefacts(project, artefacts)

    # indicates that the project and its artefacts are in Kernel
    return True


def propagate_kernel_artefacts(schema, family=None):
    '''
    Creates/updates artefacts based on the indicated Schema in Aether Kernel.
    '''

    artefacts = {
        'name': schema.project.name,
        'family': family,
        'avro_schemas': [__parse_schema(schema)],
    }

    __upsert_kernel_artefacts(schema.project, artefacts)

    # indicates that the schema linked artefacts are in Kernel
    return True


def submit_to_kernel(payload, mappingset_id, submission_id=None):
    '''
    Push the submission to Aether Kernel
    '''

    return request(
        method='put' if submission_id else 'post',
        url=__get_type_url('submissions', submission_id),
        json={
            'payload': payload,
            'mappingset': mappingset_id,
        },
        headers=get_kernel_auth_header(),
    )


def __upsert_kernel_artefacts(project, artefacts={}):
    '''
    This method pushes the project artefacts to Aether Kernel.
    '''

    project_id = str(project.project_id)

    auth_header = get_kernel_auth_header()
    if not auth_header:
        raise KernelPropagationError(MSG_KERNEL_CONNECTION_ERR)
    headers = add_instance_realm_in_headers(project, auth_header)

    kernel_url = get_kernel_url()
    url = f'{kernel_url}/projects/{project_id}/avro-schemas/'

    response = request(method='patch', url=url, json=artefacts, headers=headers)
    if response.status_code != 200:
        content = response.content.decode('utf-8')
        raise KernelPropagationError(
            MSG_KERNEL_RESPONSE_ERR.format(project_id=project_id, content=content)
        )

    return True


def __parse_schema(schema):
    return {
        'id': str(schema.kernel_id),
        'definition': schema.avro_schema,
    }


def __get_type_url(model_type, id=None):
    '''
    Returns Aether Kernel url for type "XXX"
    '''
    if not id:
        return '{kernel_url}/{type}/'.format(
            kernel_url=get_kernel_url(),
            type=model_type,
        )
    else:
        return '{kernel_url}/{type}/{id}/'.format(
            kernel_url=get_kernel_url(),
            type=model_type,
            id=id,
        )
