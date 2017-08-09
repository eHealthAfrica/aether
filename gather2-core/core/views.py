from django.contrib.auth import get_user_model
from django.db.models import Count, Min, Max
from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from . import models, serializers


class SurveyViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    You can search by *survey name*, *created by username* or within the *schema*.

    Create a new survey in the [json-schema standard](http://json-schema.org/examples.html).

    Example:

        {
            "title": "Example Schema",
            "type": "object",
            "properties": {
                "firstName": {
                    "type": "string"
                },
                "lastName": {
                    "type": "string"
                },
                "age": {
                    "description": "Age in years",
                    "type": "integer",
                    "minimum": 0
                }
            },
            "required": ["firstName", "lastName"]
        }
    '''

    queryset = models.Survey.objects.all()
    serializer_class = serializers.SurveySerializer

    search_fields = ('name', 'created_by__username', 'schema',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)


class ResponseViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    All the responses to surveys.

    You can search by *survey name*, *created by username* or within the *data*.
    '''

    queryset = models.Response.objects.all()
    serializer_class = serializers.ResponseSerializer

    search_fields = ('survey__name', 'created_by__username', 'data',)
    ordering_fields = ('survey', 'created',)
    ordering = ('survey',)

    def get_queryset(self):
        # Eventually replace this naive implementation with a
        # django-restframework-filters + django-filter version that supports JSONField
        orig_qs = super(ResponseViewSet, self).get_queryset()

        data_queries = dict([
            (k, v)
            for (k, v) in self.request.query_params.items()
            if k.startswith('data__')
        ])

        return orig_qs.filter(**data_queries)

    def get_serializer(self, *args, **kwargs):
        '''
        Use the parent relationship, if available, on the child resource
        '''
        # Needed by ODK-Importer submission

        # fixes "AttributeError: This QueryDict instance is immutable"
        self.request.POST._mutable = True
        kwargs.get('data', {}).update(self.get_parents_query_dict())
        return super(ResponseViewSet, self).get_serializer(*args, **kwargs)


class AttachmentViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    All the attachments belonging to responses.

    You can search by *attachment name*.
    '''

    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)

    def get_serializer(self, *args, **kwargs):
        '''
        Use the parent relationship, if available, on the child resource
        '''
        # Needed by ODK-Importer submission

        # fixes "AttributeError: This QueryDict instance is immutable"
        self.request.POST._mutable = True
        kwargs.get('data', {}).update(self.get_parents_query_dict())
        return super(AttachmentViewSet, self).get_serializer(*args, **kwargs)


class MapFunctionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    All the map function linked to surveys.

    You can search by *survey name*, or within the *code*.

    The *code* should be a python scriptlet. The only global variable is `data`.
    `data` represents the response data.

    Example:

        print data["firstName"]

    '''

    queryset = models.MapFunction.objects.all()
    serializer_class = serializers.MapFunctionSerializer

    search_fields = ('survey__name', 'code')
    ordering_fields = ('survey', 'created',)
    ordering = ('survey',)


class MapResultViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    '''
    The results produce by a map function and the responses linked to the survey.
    There should be one result per map function and response. This process is
    automatic without user interaction.

    You can search within the *output* or even the *error*.
    '''

    queryset = models.MapResult.objects.all()
    serializer_class = serializers.MapResultSerializer

    search_fields = ('output', 'error',)
    ordering_fields = ('response', 'map_function', 'created',)
    ordering = ('response',)


class ReduceFunctionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    All the reduce function linked to map functions.

    You can search within the *code*, the *output* or even the *error*.

    The *code* should be a python scriptlet. The only global variable is `data`.
    `data` contains all the results produced by the map function and the responses.

    Example:

        print '-'.join(d for d in data if d)

    '''

    queryset = models.ReduceFunction.objects.all()
    serializer_class = serializers.ReduceFunctionSerializer

    search_fields = ('code', 'output', 'error',)
    ordering_fields = ('map_function', 'created',)
    ordering = ('map_function',)


class SurveyStatsViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    '''
    Contains the aggregated data from survey responses like:

    - first response date
    - last response date
    - number of responses

    '''

    queryset = models.Survey.objects.all()
    serializer_class = serializers.SurveyStatsSerializer

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)

    def get_queryset(self):
        return models.Survey \
                     .objects \
                     .values('id', 'name', 'schema', 'created', 'created_by_id') \
                     .annotate(
                         first_response=Min('responses__created'),
                         last_response=Max('responses__created'),
                         responses=Count('responses__id'),
                     )


class UserViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    search_fields = ('username', 'email',)
    ordering = ('username',)
