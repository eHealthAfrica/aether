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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import requests

from aether.common.kernel.utils import get_auth_header, get_kernel_server_url


class KernelReplicationError(Exception):
    pass


def replicate_project(project):
    '''
    Replicates the indicated project in Aether Kernel.
    '''

    item_id = str(project.project_id)
    # because the name is unique use an unexpected one
    item_name = f'aether.odk.xforms: {item_id}'

    __upsert_item(
        item_model='projects',
        item_id=item_id,
        item_new={
            'id': item_id,
            'name': item_name,
            'revision': '1',
        },
        # no need to update any property there
        item_update=None,
    )

    # indicates that the item is in Kernel
    return True


def replicate_xform(xform):
    '''
    Replicates the indicated xForm in Aether Kernel.

    One XForm should create in Kernel:
        - one Mapping,
        - one Schema and
        - one ProjectSchema.
    '''

    # 1. make sure that the project already exists in Kernel
    replicate_project(xform.project)

    # all the replicated items will have the same id
    item_id = str(xform.kernel_id)
    # because the name is unique use an unexpected one
    item_name = f'aether.odk.xforms: {item_id}'
    project_id = str(xform.project.project_id)

    # 2. check mapping (this links the xForm submissions with the mapping)
    __upsert_item(
        item_model='mappings',
        item_id=item_id,
        item_new={
            'id': item_id,
            'name': item_name,
            'revision': xform.version,
            'project': project_id,
            'definition': {'mappings': []},
        },
        # make sure that the project id is the expected one
        item_update={
            'project': project_id,
        },
    )

    # 3. check schema (creates the entity definition for the xForm)
    __upsert_item(
        item_model='schemas',
        item_id=item_id,
        item_new={
            'id': item_id,
            'name': item_name,
            'revision': xform.version,
            'definition': xform.avro_schema,
            'type': 'xform',
        },
        item_update={
            'revision': xform.version,
            'definition': xform.avro_schema,
            'type': 'xform',
        },
    )

    # 4. check project schema (this links the schema with the project)
    __upsert_item(
        item_model='projectschemas',
        item_id=item_id,
        item_new={
            'id': item_id,
            'name': item_name,
            'project': project_id,
            'schema': item_id,
        },
        # make sure that the ids are the expected ones
        item_update={
            'project': project_id,
            'schema': item_id,
        },
    )

    # indicates that the items are in Kernel
    return True


def __upsert_item(item_model, item_id, item_new, item_update=None):
    '''
    This methods checks the existence of the item in Aether Kernel.

    If it doesn't exist creates it otherwise updates its properties.
    '''

    auth_header = get_auth_header()
    if not auth_header:
        raise KernelReplicationError('Connection with Aether Kernel server is not possible.')

    kernel_url = get_kernel_server_url()
    url = f'{kernel_url}/{item_model}/{item_id}.json'

    response = requests.get(url=url, headers=auth_header)
    content = response.content.decode('utf-8')

    # the only acceptable responses are 200 or 404
    if response.status_code not in (200, 404):
        raise KernelReplicationError(
            'Unexpected response from Aether Kernel server '
            f'while trying to check the existence of the {item_model[:-1]} with id {item_id}.\n'
            f'Response: {content}'
        )

    if response.status_code == 200:
        if not item_update:  # if not provided then no need to update
            return True

        # already exists, update it with the given item
        item_kernel = json.loads(content)
        for k, v in item_update.items():
            item_kernel[k] = v
        response_put = requests.put(url=url, json=item_kernel, headers=auth_header)
        if response_put.status_code != 200:
            content_put = response_put.content.decode('utf-8')
            raise KernelReplicationError(
                'Unexpected response from Aether Kernel server '
                f'while trying to update the {item_model[:-1]} with id {item_id}.\n'
                f'Response: {content_put}'
            )

    if response.status_code == 404:
        # it does not exist yet, create it
        url_post = f'{kernel_url}/{item_model}.json'
        response_post = requests.post(url=url_post, json=item_new, headers=auth_header)
        content_post = response_post.content.decode('utf-8')

        if response_post.status_code != 201:
            raise KernelReplicationError(
                'Unexpected response from Aether Kernel server '
                f'while trying to create the {item_model[:-1]} with id {item_id}.\n'
                f'Response: {content_post}'
            )

    # indicates that the item is in Kernel
    return True
