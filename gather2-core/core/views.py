from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from .serializers import SurveySerializer, ResponseSerializer, MapFunctionSerializer, MapResultSerializer, ReduceFunctionSerializer
from .models import Survey, Response, MapResult, MapFunction, ReduceFunction
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


# This disabled CSRF checks only on the survey API calls.
class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class TemplateNameMixin:

    '''
    For the given ViewClass return [viewclass_list.html, viewclass.html]
    as the list of templates to try.
    '''

    def get_template_names(self):
        return ['%s_%s.html' % (self.__class__.__name__.lower(), self.action),
                '%s.html' % self.__class__.__name__.lower()]


class SurveyViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
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
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class ResponseViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    '''
    All the responses to surveys.
    '''
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
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


class MapFunctionViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = MapFunction.objects.all()
    serializer_class = MapFunctionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class MapResultViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = MapResult.objects.all()
    serializer_class = MapResultSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ReduceFunctionViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = ReduceFunction.objects.all()
    serializer_class = ReduceFunctionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
