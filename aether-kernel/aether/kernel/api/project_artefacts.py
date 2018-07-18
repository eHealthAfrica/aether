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

import random
import string

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .models import Project, Schema, ProjectSchema, Mapping


def get_project_artefacts(project):
    '''
    Returns the list of project and all its artefact ids by type.
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
def upsert_project_artefacts(
    action='upsert',
    project_id=None,
    project_name=None,
    schemas=[],
    mappings=[],
):
    '''
    Creates or updates the project and its artefacts: schemas, project schemas and mappings.

    Returns the list of project and its affected artefact ids by type.
    '''

    results = {
        'project': None,
        'schemas': set(),
        'project_schemas': set(),
        'mappings': set(),
    }

    # 1. create/update the project
    project = __upsert_instance(
        model=Project,
        pk=project_id,
        ignore_fields=['name'],  # do not update the name if the project already exists
        action=action,
        name=project_name or __random_name(),
    )
    results['project'] = str(project.pk)

    # 2. create/update the list of schemas and assign them to the project
    for raw_schema in schemas:
        schema = __upsert_instance(
            model=Schema,
            pk=raw_schema.get('id'),
            ignore_fields=['name'],
            action=action,
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
            project_schema = __upsert_instance(
                model=ProjectSchema,
                pk=schema.pk,
                project=project,
                schema=schema,
                name=schema.name,
            )
        results['project_schemas'].add(str(project_schema.pk))

    # 3. create/update the list of mappings
    for raw_mapping in mappings:
        # in case of no mappings rules were indicated, do not update them.
        ignore_fields = ['name']
        if raw_mapping.get('definition') is None:
            ignore_fields.append('definition')

        mapping = __upsert_instance(
            model=Mapping,
            pk=raw_mapping.get('id'),
            ignore_fields=ignore_fields,
            action=action,
            name=raw_mapping.get('name', __random_name()),
            definition=raw_mapping.get('definition', {'mappings': []}),
            project=project,
        )
        results['mappings'].add(str(mapping.pk))

    return results


def __upsert_instance(model, pk=None, ignore_fields=[], action='upsert', **values):
    '''
    Creates or updates an instance of the indicated Model.

    Arguments:

    - ``model``          -- the model class.
    - ``pk``             -- the primary key value of the instance, can be None.
    - ``ignore_fields``  -- if the instance already exists then these fields are not updated.
    - ``action``         -- "create" create new ones but not update, otherwise create or update.
    - ``values``         -- the named list of instance values.
    '''

    is_new = True
    if not pk:
        item = model()
    else:
        # ``update_or_create``` could be an option but if we have a
        # list of `ignore_fields` that method will override them.
        # We need those values only in case of creation because they are required,
        # but we don't want to change them in any other circumstances.
        # An example would be the AVRO schema generated by the ODK module
        # and the mapping rules generated by the UI app.
        # This is a collaborative app where each part has a main task and all
        # of them work together to achive a common goal.
        try:
            item = model.objects.get(pk=pk)
            is_new = False
        except ObjectDoesNotExist:
            item = model(pk=pk)

    # restrict the list of fields that can be assigned
    fields = [
        f.name
        for f in model._meta.fields
        if is_new or f.name not in ignore_fields
    ]

    # assign indicated values
    for k, v in values.items():
        if k in fields:
            setattr(item, k, v)

    if is_new or action != 'create':
        # if is new first check that the same name is not there
        # otherwise append a numeric suffix or a random string to it
        if is_new:
            item.name = __right_pad(model, item.name)
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


def __right_pad(model, value):
    '''
    Creates a numeric or a random string suffix for the given value
    '''
    numeric_suffix = 0
    new_value = value

    while model.objects.filter(name=new_value[:50]).exists():
        if len(new_value) > 50:
            # in case of name size overflow
            return (f'{value} - {__random_name()}')[:50]
        numeric_suffix += 1
        new_value = f'{value}_{numeric_suffix}'

    return new_value[:50]
