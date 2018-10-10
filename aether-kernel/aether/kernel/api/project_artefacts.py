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

from .models import Project, Schema, ProjectSchema, MappingSet, Mapping
from .avro_tools import avro_schema_to_passthrough_artefacts as parser


NAME_MAX_SIZE = 50


def get_project_artefacts(project):
    '''
    Returns the list of project and all its artefact ids by type.
    '''

    results = {
        'project': str(project.pk),
        'schemas': set(),
        'project_schemas': set(),
        'mappingsets': set(),
        'mappings': set(),
    }
    for mappingset in MappingSet.objects.filter(project=project):
        results['mappingsets'].add(str(mappingset.pk))
        for mapping in Mapping.objects.filter(mappingset=mappingset):
            results['mappings'].add(str(mapping.pk))

    for project_schema in ProjectSchema.objects.filter(project=project):
        results['schemas'].add(str(project_schema.schema.pk))
        results['project_schemas'].add(str(project_schema.pk))

    return results


@transaction.atomic
def upsert_project_artefacts(
    action='upsert',
    project_id=None,
    project_name=None,
    schemas=[],
    mappingsets=[],
    mappings=[],
):
    '''
    Creates or updates the project and its artefacts:
        schemas,
        project schemas,
        mapping sets and
        mappings.

    Returns the list of project and its affected artefact ids by type.
    '''

    results = {
        'project': None,
        'schemas': set(),
        'project_schemas': set(),
        'mappingsets': set(),
        'mappings': set(),
    }
    # keeps the list of created project schemas and their ids
    # with those the list of used entities in the mapping rules can be filled
    mapping_project_schemas = {}

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
        # by default use the given name, otherwise the generated one
        mapping_project_schemas[raw_schema.get('name', project_schema.name)] = str(project_schema.pk)

    # 3. create/update the mapping sets
    for raw_mappingset in mappingsets:
        ignore_fields = ['name']
        if raw_mappingset.get('input') is None:
            # in case of no input were indicated, do not update it.
            ignore_fields.append('input')

        mappingset = __upsert_instance(
            model=MappingSet,
            pk=raw_mappingset.get('id'),
            ignore_fields=ignore_fields,
            action=action,
            name=raw_mappingset.get('name', __random_name()),
            input=raw_mappingset.get('input', {}),
            project=project,
        )
        results['mappingsets'].add(str(mappingset.pk))

    # 4. create/update the mappings
    for raw_mapping in mappings:
        ignore_fields = ['name']
        mapping_name = raw_mapping.get('name', __random_name())

        mapping_definition = raw_mapping.get('definition')
        if mapping_definition is None:
            # in case of no mapping rules were indicated, do not update them.
            ignore_fields.append('definition')
            mapping_definition = {'mapping': [], 'entities': {}}

        elif 'entities' not in mapping_definition:
            # find out the list of used entities (project schemas) within these rules
            used_schemas = []
            for mapping in mapping_definition.get('mapping', []):
                # [ '$.property_name', 'EntityName.another_property_name' ]
                schema_name = mapping[1].split('.')[0]
                if not len(list(filter(lambda x: x == schema_name, used_schemas))):
                    used_schemas.append(schema_name)
            used_mapping_project_schemas = {}
            for used_schema in used_schemas:
                used_mapping_project_schemas[used_schema] = mapping_project_schemas.get(used_schema)
            mapping_definition = {
                'mapping': mapping_definition.get('mapping', []),
                'entities': used_mapping_project_schemas,
            }

        # check for the mapping set
        mappingset_id = raw_mapping.get('mappingset', raw_mapping.get('id'))
        try:
            mappingset = MappingSet.objects.get(pk=mappingset_id)
        except ObjectDoesNotExist:
            mappingset = __upsert_instance(
                model=MappingSet,
                pk=mappingset_id,
                action=action,
                name=mapping_name,  # use same name as mapping
                input=raw_mapping.get('input', {}),
                project=project,
            )
        results['mappingsets'].add(str(mappingset.pk))

        mapping = __upsert_instance(
            model=Mapping,
            pk=raw_mapping.get('id'),
            ignore_fields=ignore_fields,
            action=action,
            name=mapping_name,
            definition=mapping_definition,
            mappingset=mappingset,
            is_read_only=raw_mapping.get('is_read_only', False),
            is_active=raw_mapping.get('is_active', True),
            project=project,
        )
        results['mappings'].add(str(mapping.pk))

    return results


def upsert_project_with_avro_schemas(
    action='upsert',
    project_id=None,
    project_name=None,
    avro_schemas=[],
):
    '''
    Creates or updates the project and links it with the given AVRO schemas
    and related artefacts: project schemas and passthrough mappings.

    Returns the list of project and its affected artefact ids by type.
    '''

    schemas = []
    mappings = []

    for avro_schema in avro_schemas:
        schema, mapping = parser(avro_schema.get('id'), avro_schema.get('definition'))
        schemas.append(schema)
        mappings.append(mapping)

        # Include an empty mapping if the schema is new
        id = schema.get('id')
        if not Schema.objects.filter(pk=id).exists():
            mappings.append({
                # even being the same name it's going to append the suffix `-1`
                'name': schema.get('name'),
                # the passthrough mapping has created a mappingset with this id
                'mappingset': id,
            })

    return upsert_project_artefacts(
        action=action,
        project_id=project_id,
        project_name=project_name,
        schemas=schemas,
        mappings=mappings,
    )


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

    # with new instances first check that the same name is not already in use
    # otherwise append a numeric suffix or a random string to it
    if is_new:
        item.name = __right_pad(model, item.name)

    if is_new or action != 'create':
        item.save()

    item.refresh_from_db()
    return item


def __random_name():
    '''
    Creates a random string of length 50.
    '''
    # Names are unique so we try to avoid annoying errors with duplicated names.
    alphanum = string.ascii_letters + string.digits
    return ''.join([random.choice(alphanum) for x in range(NAME_MAX_SIZE)])


def __right_pad(model, name):
    '''
    Creates a numeric or a random string suffix for the given name
    '''
    SEP = '-'

    numeric_suffix = 0
    new_name = name.strip()

    while model.objects.filter(name=new_name[:NAME_MAX_SIZE]).exists():
        if len(new_name) > NAME_MAX_SIZE:  # in case of name size overflow
            break
        numeric_suffix += 1
        new_name = f'{name}{SEP}{numeric_suffix}'

    if model.objects.filter(name=new_name[:NAME_MAX_SIZE]).exists():
        # we cannot add any suffix to the name and is already in use
        # solution, take only a piece of the name and append a random string
        piece = name[:(NAME_MAX_SIZE - 17)]  # 16 random chars should be enough
        return (f'{piece}{SEP}{__random_name()}')[:NAME_MAX_SIZE]

    return new_name[:NAME_MAX_SIZE]
