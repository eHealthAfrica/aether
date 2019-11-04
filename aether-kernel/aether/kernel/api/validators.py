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

from django.core.exceptions import ValidationError
from aether.python import exceptions, validators
from django.utils.translation import ugettext as _

from .redis import in_same_project_and_cache


def wrapper_validate_avro_schema(data):
    try:
        return validators.validate_avro_schema(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve.message)


def wrapper_validate_schemas(data):
    try:
        return validators.validate_schemas(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve.message)


def wrapper_validate_mapping_definition(data):
    try:
        return validators.validate_mapping_definition(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve)


def wrapper_validate_schema_definition(data):
    try:
        return validators.validate_schema_definition(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve)


def validate_entity_project(validated_data, ignore_submission_check=False):
    from .models import Project

    _schema_decorator = validated_data.get('schemadecorator')
    _submission = validated_data.get('submission')
    _mapping = validated_data.get('mapping')
    _possible_project = None
    _artefacts_in_same_project = True

    if _schema_decorator:
        _possible_project = Project.objects.filter(schemadecorators__pk=_schema_decorator.pk).first()
    elif _submission:
        _possible_project = Project.objects.filter(submissions__pk=_submission.pk).first()
    elif _mapping:
        _possible_project = Project.objects.filter(mappings__pk=_mapping.pk).first()

    if _possible_project:
        _submission_id = str(_submission.pk) if _submission else None
        if ignore_submission_check:
            _submission_id = None
        _artefact_dict = {
            'schema_decorators': str(_schema_decorator.pk) if _schema_decorator else None,
            'submissions': _submission_id,
            'mappings': str(_mapping.pk) if _mapping else None,
        }
        _artefacts_in_same_project = in_same_project_and_cache(_artefact_dict, _possible_project)
    else:
        raise ValidationError(
            _('No associated project. Check you provided the correct Submission, Mapping and Schema Decorator')
        )

    if not _artefacts_in_same_project:
        raise ValidationError(
            _('Submission, Mapping and Schema Decorator MUST belong to the same Project')
        )

    return _possible_project
