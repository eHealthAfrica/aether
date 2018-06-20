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


class KernelPropagationError(Exception):
    pass


def propagate_kernel_project(project):
    '''
    Creates a copy of the indicated project in Aether Kernel
    and creates/updates its linked artefacts.
    '''

    artefacts = {
        'schemas': [],
        'mappings': [],
    }

    for xform in project.xforms.all():
        schema, mapping = __xform_to_artefacts(xform)
        artefacts['schemas'].append(schema)
        artefacts['mappings'].append(mapping)

    __upsert_kernel_artefacts(project, artefacts)

    # indicates that the project and its artefacts are in Kernel
    return True


def propagate_kernel_artefacts(xform):
    '''
    Creates/updates artefacts based on the indicated xForm in Aether Kernel.

    One XForm should create/update in Kernel:
        - one Project,
        - one Mapping,
        - one Schema and
        - one ProjectSchema.
    '''

    schema, mapping = __xform_to_artefacts(xform)
    artefacts = {
        'schemas': [schema],
        'mappings': [mapping],
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

    kernel_url = get_kernel_server_url()
    url = f'{kernel_url}/projects/{project_id}/artefacts/'

    response = requests.patch(url=url, json=artefacts, headers=auth_header)
    if response.status_code != 200:
        content = response.content.decode('utf-8')
        raise KernelPropagationError(
            MSG_KERNEL_RESPONSE_ERR.format(project_id=project_id, content=content)
        )

    return True


def __xform_to_artefacts(xform):
    # all the items will have the same id
    item_id = str(xform.kernel_id)

    schema = {'id': item_id, 'definition': xform.avro_schema}
    mapping = {'id': item_id}

    return schema, mapping
