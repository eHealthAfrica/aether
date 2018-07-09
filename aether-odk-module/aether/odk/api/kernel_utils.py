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
import random
import requests
import string

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
        # do not update the mapping rules in case of the xform was already propagated
        # that might be the case that the user changed the default rules
        'action': 'create',
        'name': __right_pad(project.name),
        'schemas': [],
        'mappings': [],
    }

    for xform in project.xforms.order_by('-modified_at'):
        schemas, mapping = __xform_to_artefacts(xform)
        artefacts['schemas'] += schemas
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
        - one or more Schemas and
        - one or more ProjectSchemas.
    '''

    schemas, mapping = __xform_to_artefacts(xform)
    artefacts = {
        # do not update the mapping rules in case of the xform was already propagated
        # that might be the case that the user changed the default rules
        'action': 'create',
        'name': __right_pad(xform.project.name),
        'schemas': schemas,
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
    definition = copy.deepcopy(xform.avro_schema)

    name = definition['name']
    fields = definition['fields']

    # create identity mapping rules using the AVRO schema fields (first level)
    rules = [
        [
            '{}.{}'.format('$', f['name']),   # source
            '{}.{}'.format(name, f['name']),  # destination
        ]
        for f in fields
    ]

    # kernel entities/ schemas need an "id" field,
    # if this does not exist include it manually
    id_or_none = next((x for x in fields if x['name'] == 'id'), None)
    if id_or_none is None:
        rules.append([
            '#!uuid',  # this will generate an UUID during entity extractor step
            f'{name}.id',
        ])
        definition['fields'].append({
            'name': 'id',
            'doc': _('ID'),
            'type': 'string',
        })

    random_name = __right_pad(name)
    schema = {
        'id': item_id,
        'name': random_name,
        'definition': definition,
    }
    mapping = {
        'id': item_id,
        'name': random_name,
        'definition': {
            'entities': {name: item_id},
            'mapping': rules,
        }
    }

    return [schema], mapping


def __right_pad(value):
    '''
    Creates a random string of length 50 and appends it to the given value
    '''
    alphanum = string.ascii_letters + string.digits
    pad = ''.join([random.choice(alphanum) for x in range(50)])
    return (f'{value}__{pad}')[0:50]
