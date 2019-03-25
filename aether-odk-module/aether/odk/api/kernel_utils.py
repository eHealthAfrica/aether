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

from django.utils.translation import ugettext as _

from aether.common.kernel.utils import get_auth_header, get_kernel_server_url
from aether.common.multitenancy.utils import add_instance_realm_in_headers
from aether.common.utils import request

# list of messages that can be translated
MSG_KERNEL_CONNECTION_ERR = _(
    'Connection with Aether Kernel server is not possible.'
)
MSG_KERNEL_RESPONSE_ERR = _(
    'Unexpected response from Aether Kernel server '
    'while trying to create/update the project artefacts "{project_id}".\n'
    'Response: {content}'
)

NAMESPACE = 'org.ehealthafrica.aether.odk.xforms'


class KernelPropagationError(Exception):
    pass


def propagate_kernel_project(project, family=None):
    '''
    Creates a copy of the indicated project in Aether Kernel
    and creates/updates its linked artefacts based on the given AVRO schemas.

    One AVRO schema should create/update in Kernel:
        - one Project,
        - one Mapping,
        - one Schema and
        - one ProjectSchema.
    '''

    artefacts = {
        'name': project.name,
        'family': family,
        'avro_schemas': [],
    }

    for xform in project.xforms.order_by('-modified_at'):
        artefacts['avro_schemas'].append(__parse_xform(xform))

    __upsert_kernel_artefacts(project, artefacts)

    # indicates that the project and its artefacts are in Kernel
    return True


def propagate_kernel_artefacts(xform, family=None):
    '''
    Creates/updates artefacts based on the indicated xForm in Aether Kernel.
    '''

    artefacts = {
        'name': xform.project.name,
        'family': family,
        'avro_schemas': [__parse_xform(xform)],
    }

    __upsert_kernel_artefacts(xform.project, artefacts)

    # indicates that the xform linked artefacts are in Kernel
    return True


def __upsert_kernel_artefacts(project, artefacts={}):
    '''
    This method pushes the project artefacts to Aether Kernel.
    '''

    project_id = str(project.project_id)

    auth_header = get_auth_header()
    if not auth_header:
        raise KernelPropagationError(MSG_KERNEL_CONNECTION_ERR)
    headers = add_instance_realm_in_headers(project, auth_header)

    kernel_url = get_kernel_server_url()
    url = f'{kernel_url}/projects/{project_id}/avro-schemas/'

    response = request(method='patch', url=url, json=artefacts, headers=headers)
    if response.status_code != 200:
        content = response.content.decode('utf-8')
        raise KernelPropagationError(
            MSG_KERNEL_RESPONSE_ERR.format(project_id=project_id, content=content)
        )

    return True


def __parse_xform(xform):
    definition = copy.deepcopy(xform.avro_schema)
    # assign namespace based on project name
    definition['namespace'] = f'{NAMESPACE}.{__clean_name(xform.project.name)}'

    return {
        'id': str(xform.kernel_id),
        'definition': definition,
    }


def __clean_name(value):
    '''
    Replaces any non alphanumeric character with spaces
    Converts to title case
    Removes spaces
    '''
    return ''.join([c if c.isalnum() else ' ' for c in value]).title().replace(' ', '')
