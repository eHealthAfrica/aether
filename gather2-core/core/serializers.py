# -*- coding: utf-8 -*-
import json
import logging
import string

import jsonschema
from rest_framework import serializers

from .models import MapFunction, MapResult, ReduceFunction, Response, Survey, Attachment


logger = logging.getLogger(__name__)


# Note: a combinations of JSONB in postgres and json parsing gives a nasty db
# error
# See: https://bugs.python.org/issue10976#msg159391
# and
# http://www.postgresql.org/message-id/E1YHHV8-00032A-Em@gemulon.postgresql.org
def make_printable(obj):
    if isinstance(obj, dict):
        return {make_printable(k): make_printable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_printable(elem) for elem in obj]
    elif isinstance(obj, str):
        # Only printables
        return ''.join(x for x in obj if x in string.printable)
    else:
        return obj


class JSONSerializerMixin:

    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                raise serializers.ValidationError(str(e))

        return make_printable(data)

    def to_representation(self, value):
        class JSONish(type(value)):

            """
            Helper class to properly render JSON in the HTML form.
            Without this it will either put the JSON as a string in the json response
            or it will put a pyhton dict as a string in html and json renders
            """

            def __str__(self):
                return json.dumps(self, sort_keys=True)

        return JSONish(value)


class JSONSerializer(JSONSerializerMixin, serializers.Serializer):
    pass


class JSONSerializerField(JSONSerializerMixin, serializers.CharField):
    pass


def is_json(value):
    if isinstance(value, str):
        try:
            json.loads(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
    return True


class JSONSpecValidator(object):

    """
    This validates the submitted json with the schema saved on the Response.Survey.schema
    """

    def __init__(self):
        self.schema = {}

    def __call__(self, value):
        v = jsonschema.Draft4Validator(self.schema)
        errors = sorted(v.iter_errors(value), key=lambda e: e.path)
        if errors:
            raise serializers.ValidationError(list(map(str, errors)))
        return True

    def set_context(self, serializer_field):
        survey_id = serializer_field.parent.initial_data.get('survey')
        # First (only) or None
        survey = (Survey.objects.filter(id=survey_id) or [None])[0]
        if survey:
            self.schema = survey.schema


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('attachment-detail')
    response_url = serializers.HyperlinkedRelatedField(
        'response-detail', source='response', read_only=True)

    class Meta:
        model = Attachment
        fields = ['id', 'url', 'attachment_file', 'name', 'response', 'response_url']


class SurveySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('survey-detail')
    map_functions_url = serializers.HyperlinkedIdentityField(
        'survey_map_function-list', read_only=True, lookup_url_kwarg='parent_lookup_survey')
    responses_url = serializers.HyperlinkedIdentityField(
        'survey_response-list', read_only=True, lookup_url_kwarg='parent_lookup_survey')
    schema = JSONSerializerField(validators=[is_json])
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())

    class Meta:
        model = Survey
        fields = ['id', 'url', 'schema', 'name', 'responses_url', 'map_functions_url', 'created_by']
        read_only_fields = ['id', 'url', 'responses_url', 'map_functions_url', 'created_by']


class ResponseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('response-detail')
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail', source='survey', read_only=True)
    data = JSONSerializerField(validators=[JSONSpecValidator()],
                               style={'base_template': 'schema_field.html'})
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())
    attachments_url = serializers.HyperlinkedIdentityField(
        'response_attachment-list', read_only=True, lookup_url_kwarg='parent_lookup_response')

    class Meta:
        model = Response
        fields = '__all__'


class MapFunctionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('map_function-detail')
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail', source='survey', read_only=True)
    results_url = serializers.HyperlinkedIdentityField(
        'map_function_result-list', read_only=True, lookup_url_kwarg='parent_lookup_map_function')
    reduce_functions_url = serializers.HyperlinkedIdentityField(
        'map_reduce_function-list', read_only=True, lookup_url_kwarg='parent_lookup_map_function')

    class Meta:
        model = MapFunction
        fields = '__all__'


class MapResultSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('map_results-detail')
    response_url = serializers.HyperlinkedRelatedField(
        'response-detail', source='response', read_only=True)
    map_functions_url = serializers.HyperlinkedRelatedField(
        'map_function-detail', source='map_function', read_only=True)

    class Meta:
        model = MapResult
        fields = '__all__'


class ReduceFunctionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('reduce_function-detail')
    map_functions_url = serializers.HyperlinkedRelatedField(
        'map_function-detail', source='map_function', read_only=True)

    class Meta:
        model = ReduceFunction
        fields = '__all__'
