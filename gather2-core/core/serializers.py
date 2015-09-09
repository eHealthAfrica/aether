from rest_framework import serializers
import json
import logging
from .models import SurveyItem, Survey
import jsonschema


logger = logging.getLogger(__name__)


class JSONSerializerField(serializers.Field):

    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return data

    def to_representation(self, value):

        class JSONy(type(value)):

            """
            Helper class to properly render JSON in the HTML form.
            Without this it will either put the JSON as a string in the json response
            or it will put a pyhton dict as a string in html and json renders
            """

            def __str__(self):
                return json.dumps(self, sort_keys=True)

        return JSONy(value)


def is_json(value):
    if isinstance(value, str):
        try:
            json.loads(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
    return True


class JSONSpecValidator(object):

    """
    This validates the submitted json with the schema saved on the SurveyItem.Survey.schema
    """

    def __init__(self):
        self.schema = None

    def __call__(self, value):
        v = jsonschema.Draft4Validator(self.schema)
        errors = sorted(v.iter_errors(value), key=lambda e: e.path)
        if errors:
            raise serializers.ValidationError(list(map(str, errors)))
        return True

    def set_context(self, serializer_field):

        schema = None
        if serializer_field.parent.instance:
            # This is hard coded currently.
            schema = serializer_field.parent.instance.survey.schema

        try:
            self.schema = schema
        except Exception as e:
            raise serializers.ValidationError(str(e))


class SurveySerialzer(serializers.HyperlinkedModelSerializer):
    schema = JSONSerializerField(validators=[is_json])

    class Meta:
        model = Survey


class SurveyItemSerialzer(serializers.HyperlinkedModelSerializer):
    data = JSONSerializerField(validators=[JSONSpecValidator()])

    class Meta:
        model = SurveyItem
