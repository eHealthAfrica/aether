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

import random
import string

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .models import Project, Schema, ProjectSchema, Mapping


def get_project_artefacts(project):
    '''
    Returns the list of project and all its artefacts ids by type.
    '''

    results = {
        'project': str(project.pk),
        'schemas': set(),
        'project_schemas': set(),
        'mappings': set(),
    }

    for project_schema in ProjectSchema.objects.filter(project=project):
        results['schemas'].add(str(project_schema.schema.pk))
        results['project_schemas'].add(str(project_schema.pk))

    for mapping in Mapping.objects.filter(project=project):
        results['mappings'].add(str(mapping.pk))

    return results


@transaction.atomic
def upsert_project_artefacts(project_id=None, project_name=None, schemas=[], mappings=[]):
    '''
    Creates or updates the project and its artefacts: schemas, project schemas and mappings.

    Returns the list of project and its affected artefacts ids by type.
    '''

    results = {
        'project': None,
        'schemas': set(),
        'project_schemas': set(),
        'mappings': set(),
    }

    # 1. create/update the project
    project = __upsert_instance(
        Model=Project,
        pk=project_id,
        ignore_fields=['name'],  # do not update the name if the project already exists
        name=project_name or __random_name(),
    )
    results['project'] = str(project.pk)

    # 2. create/update the list of schemas and assign them to the project
    for raw_schema in schemas:
        schema = __upsert_instance(
            Model=Schema,
            pk=raw_schema.get('id'),
            ignore_fields=['name'],
            name=raw_schema.get('name', __random_name()),
            definition=raw_schema.get('definition', {}),
            type=raw_schema.get('type', 'record'),
        )
        results['schemas'].add(str(schema.pk))

        # project schemas are a special case, it's useless looking for their "pk"
        # but for the relationship between project and schema
        try:
            project_schema = ProjectSchema.objects.get(project=project, schema=schema)
        except ObjectDoesNotExist:
            project_schema = ProjectSchema.objects.create(
                project=project,
                schema=schema,
                name=__random_name(),  # names are unique
            )
        results['project_schemas'].add(str(project_schema.pk))

    # 3. create/update the list of mappings
    for raw_mapping in mappings:
        # in case of no mappings rules were indicated, do not update them.
        ignore_fields = ['name']
        if raw_mapping.get('definition') is None:
            ignore_fields.append('definition')

        mapping = __upsert_instance(
            Model=Mapping,
            pk=raw_mapping.get('id'),
            ignore_fields=ignore_fields,
            name=raw_mapping.get('name', __random_name()),
            definition=raw_mapping.get('definition', {'mappings': []}),
            project=project,
        )
        results['mappings'].add(str(mapping.pk))

    return results


def __upsert_instance(Model, pk=None, ignore_fields=[], **values):
    '''
    Creates or updates an instance of the indicated Model.

    Arguments:

    - ``Model``          -- the model class.
    - ``pk``             -- the primary key value of the instance, can be None.
    - ``ignore_fields``  -- if the instance already exists then these fields are not updated.
    - ``values``         -- the named list of instance values.
    '''

    is_new = True
    if not pk:
        item = Model()
    else:
        try:
            item = Model.objects.get(pk=pk)
            is_new = False
        except ObjectDoesNotExist:
            item = Model(pk=pk)

    # restrict the list of fields that can be assigned
    fields = [
        f.name
        for f in Model._meta.fields
        if is_new or f.name not in ignore_fields
    ]

    # assign indicated values
    for k, v in values.items():
        if k in fields:
            setattr(item, k, v)

    item.save()
    item.refresh_from_db()
    return item


def __random_name():
    '''
    Creates a random string of length 50.
    '''
    # Names are unique so we try to avoid annoying errors with duplicated names.
    alphanum = string.ascii_letters + string.digits
    return ''.join([random.choice(alphanum) for x in range(50)])
