# -*- coding: utf-8 -*-
import json
import jsonschema
from django.contrib.auth import get_user_model
from rest_framework import serializers
from . import models


JSON_STYLE = {'base_template': 'textarea.html', 'rows': 10}


class JSONValidator(object):
    '''
    This validates the submitted json with the schema saved on the
    `Response.Survey.schema` or with `{"type": "object"}` for the schemas
    '''

    def __init__(self):
        self.schema = {'type': 'object'}

    def __call__(self, value):
        validation = jsonschema.Draft4Validator(self.schema)
        errors = sorted(validation.iter_errors(value), key=lambda e: e.path)
        if errors:
            raise serializers.ValidationError(list(map(str, errors)))
        return True

    def set_context(self, serializer_field):
        survey_id = serializer_field.parent.initial_data.get('survey')
        survey = models.Survey.objects.filter(pk=survey_id).first()
        if survey:
            self.schema = survey.schema


# JSONField in REST Framework
# https://github.com/encode/django-rest-framework/blob/master/rest_framework/fields.py#L1627
class JSONSerializerField(serializers.JSONField):
    '''
    Extends JSONField class and coerces to transform strings into JSON objects
    '''

    # Note: a combinations of JSONB in postgres and json parsing gives a nasty db error
    # See: https://bugs.python.org/issue10976#msg159391
    # and
    # http://www.postgresql.org/message-id/E1YHHV8-00032A-Em@gemulon.postgresql.org
    def make_printable(self, obj):
        import string

        if isinstance(obj, dict):
            return {self.make_printable(k): self.make_printable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.make_printable(elem) for elem in obj]
        elif isinstance(obj, str):
            # Only printables
            return ''.join(x for x in obj if x in string.printable)
        else:
            return obj

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                raise serializers.ValidationError(str(e))

        data = super(JSONSerializerField, self).to_internal_value(data)
        return self.make_printable(data)


class SurveySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    schema = JSONSerializerField(style=JSON_STYLE, validators=[JSONValidator()])
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    url = serializers.HyperlinkedIdentityField('survey-detail', read_only=True)
    responses_url = serializers.HyperlinkedIdentityField(
        'survey_response-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_survey'
    )
    map_functions_url = serializers.HyperlinkedIdentityField(
        'survey_map_function-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_survey'
    )

    class Meta:
        model = models.Survey
        fields = '__all__'


class ResponseSerializer(serializers.ModelSerializer):
    data = JSONSerializerField(style=JSON_STYLE, validators=[JSONValidator()])
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    url = serializers.HyperlinkedIdentityField('response-detail', read_only=True)
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail',
        source='survey',
        read_only=True
    )
    attachments_url = serializers.HyperlinkedIdentityField(
        'response_attachment-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_response'
    )

    class Meta:
        model = models.Response
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    url = serializers.HyperlinkedIdentityField('attachment-detail', read_only=True)
    response_url = serializers.HyperlinkedRelatedField(
        'response-detail',
        source='response',
        read_only=True
    )

    class Meta:
        model = models.Attachment
        fields = '__all__'


class MapFunctionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('map_function-detail', read_only=True)
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail',
        source='survey',
        read_only=True
    )
    results_url = serializers.HyperlinkedIdentityField(
        'map_function_result-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_map_function'
    )
    reduce_functions_url = serializers.HyperlinkedIdentityField(
        'map_reduce_function-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_map_function'
    )

    class Meta:
        model = models.MapFunction
        fields = '__all__'


class MapResultSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('map_results-detail', read_only=True)
    response_url = serializers.HyperlinkedRelatedField(
        'response-detail',
        source='response',
        read_only=True
    )
    map_functions_url = serializers.HyperlinkedRelatedField(
        'map_function-detail',
        source='map_function',
        read_only=True
    )

    class Meta:
        model = models.MapResult
        fields = '__all__'


class ReduceFunctionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('reduce_function-detail', read_only=True)
    map_functions_url = serializers.HyperlinkedRelatedField(
        'map_function-detail',
        source='map_function',
        read_only=True
    )

    class Meta:
        model = models.ReduceFunction
        fields = '__all__'


class SurveyStatsSerializer(serializers.ModelSerializer):
    first_response = serializers.DateTimeField()
    last_response = serializers.DateTimeField()
    responses = serializers.IntegerField()

    class Meta:
        model = models.Survey
        fields = (
            # survey fields
            'id', 'name', 'schema', 'created', 'created_by_id',
            # calculated fields
            'first_response', 'last_response', 'responses',
        )


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('user-detail', read_only=True)
    full_name = serializers.SerializerMethodField(source='get_full_name', read_only=True)

    def get_full_name(self, instance):  # pragma: no cover
        '''
        Returns a readable name of the instance.

        - ``first_name`` + ``last_name``
        - ``username``
        '''

        if instance.first_name and instance.last_name:
            return '{} {}'. format(instance.first_name, instance.last_name)

        return instance.username

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'full_name', 'email', 'url',)
