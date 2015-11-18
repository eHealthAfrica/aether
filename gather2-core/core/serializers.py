from rest_framework import serializers
import json
import logging
from .models import Response, Survey, Map
import jsonschema


logger = logging.getLogger(__name__)


class JSONSerializerMixin:

    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return data

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


class JSONSerializerField(JSONSerializerMixin, serializers.Field):
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
        survey_id = serializer_field.parent.initial_data['survey']
        # First (only) or None
        survey = (Survey.objects.filter(id=survey_id) or [None])[0]
        if survey:
            self.schema = survey.schema


class SurveySerialzer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('survey-detail')
    map_functions = serializers.HyperlinkedIdentityField(
        'survey_map_function-list', read_only=True, lookup_url_kwarg='parent_lookup_survey')
    responses = serializers.HyperlinkedIdentityField(
        'survey_response-list', read_only=True, lookup_url_kwarg='parent_lookup_survey')
    schema = JSONSerializerField(validators=[is_json])
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())

    class Meta:
        model = Survey


class ResponseSerialzer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('response-detail')
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail', source='survey', read_only=True)
    data = JSONSerializerField(validators=[JSONSpecValidator()])
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())

    class Meta:
        model = Response


class MappedResponseSerializer(ResponseSerialzer):
    #url = serializers.HyperlinkedIdentityField('map_function-detail')
    #response_url = serializers.HyperlinkedIdentityField('response-detail')
    mapped_data = JSONSerializerField()


class MapFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
