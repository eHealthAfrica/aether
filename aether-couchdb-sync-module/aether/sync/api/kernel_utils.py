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

import copy
import requests

from django.utils.translation import ugettext as _

from aether.common.kernel.utils import get_auth_header, get_kernel_server_url

# list of messages that can be translated
MSG_KERNEL_CONNECTION_ERR = _(
    'Connection with Aether Kernel server is not possible.'
)
MSG_KERNEL_RESPONSE_ERR = _(
    'Unexpected response from Aether Kernel server '
    'while trying to create/update the project artefacts "{project_id}".\n'
    'Response: {content}'
)

NAMESPACE = 'org.ehealthafrica.aether.sync.schemas'


class KernelPropagationError(Exception):
    pass


def propagate_kernel_project(project):
    '''
    Creates a copy of the indicated project in Aether Kernel
    and creates/updates its linked artefacts.
    '''

    artefacts = {
        'action': 'create',
        'name': project.name,
        'avro_schemas': [],
    }

    for json_schema in project.schemas.order_by('name'):
        artefacts['avro_schemas'].append(__schema_to_artefacts(json_schema))

    __upsert_kernel_artefacts(project, artefacts)

    # indicates that the project and its artefacts are in Kernel
    return True


def propagate_kernel_artefacts(json_schema):
    '''
    Creates/updates artefacts based on the indicated Schema in Aether Kernel.

    One JSON Schema should create/update in Kernel:
        - one Project,
        - one Mapping,
        - one Schema and
        - one Project Schema.
    '''

    artefacts = {
        'action': 'create',
        'name': json_schema.project.name,
        'avro_schemas': [__schema_to_artefacts(json_schema)],
    }

    __upsert_kernel_artefacts(json_schema.project, artefacts)

    # indicates that the schema linked artefacts are in Kernel
    return True


def __upsert_kernel_artefacts(project, artefacts={}):
    '''
    This method pushes the project artefacts to Aether Kernel.
    '''

    project_id = str(project.project_id)

    auth_header = get_auth_header()
    if not auth_header:
        raise KernelPropagationError(MSG_KERNEL_CONNECTION_ERR)

    kernel_url = get_kernel_server_url()
    url = f'{kernel_url}/projects/{project_id}/avro-schemas/'

    response = requests.patch(url=url, json=artefacts, headers=auth_header)
    if response.status_code != 200:
        content = response.content.decode('utf-8')
        raise KernelPropagationError(
            MSG_KERNEL_RESPONSE_ERR.format(project_id=project_id, content=content)
        )

    return True


def __schema_to_artefacts(json_schema):
    definition = copy.deepcopy(json_schema.avro_schema)
    # assign namespace based on project name
    if not definition.get('namespace'):
        definition['namespace'] = f'{NAMESPACE}.{__clean_name(json_schema.project.name)}'

    return {
        'id': str(json_schema.kernel_id),
        'definition': definition,
    }


def __clean_name(value):
    '''
    Replaces any non alphanumeric character with spaces
    Converts to title case
    Removes spaces
    '''
    return ''.join([c if c.isalnum() else ' ' for c in value]).title().replace(' ', '')
