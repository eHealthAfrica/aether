from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from .serializers import SurveySerializer, ResponseSerializer, MapFunctionSerializer, MapResultSerializer
from .models import Survey, Response, MapResult, MapFunction
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
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class ResponseViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


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
