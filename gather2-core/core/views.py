from rest_framework import permissions, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from .models import MapFunction, MapResult, ReduceFunction, Response, Survey, Attachment
from .serializers import (MapFunctionSerializer, MapResultSerializer,
                          ReduceFunctionSerializer, ResponseSerializer,
                          SurveySerializer, AttachmentSerializer)


class SurveyViewSet(NestedViewSetMixin, viewsets.ModelViewSet):

    '''
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
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class ResponseViewSet(NestedViewSetMixin, viewsets.ModelViewSet):

    '''
    All the responses to surveys.
    '''
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # Eventually replace this naive implementation with a
        # django-restframework-filters + django-filter version that supports
        # JSONField
        orig_qs = super(ResponseViewSet, self).get_queryset()

        data_queries = dict([
            (k, v) for (k, v) in
            self.request.query_params.items()
            if k.startswith('data__')
        ])

        filtered_qs = orig_qs.filter(**data_queries)

        return filtered_qs

    def get_serializer(self, *args, **kwargs):
        """Use the parent relationship, if available, on the child resource"""
        kwargs.get('data', {}).update(self.get_parents_query_dict())
        return super(ResponseViewSet, self).get_serializer(*args, **kwargs)


class AttachmentViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer(self, *args, **kwargs):
        """Use the parent relationship, if available, on the child resource"""
        kwargs.get('data', {}).update(self.get_parents_query_dict())
        return super(AttachmentViewSet, self).get_serializer(*args, **kwargs)


class MapFunctionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = MapFunction.objects.all()
    serializer_class = MapFunctionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class MapResultViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = MapResult.objects.all()
    serializer_class = MapResultSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ReduceFunctionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = ReduceFunction.objects.all()
    serializer_class = ReduceFunctionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
