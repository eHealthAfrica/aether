from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from .serializers import SurveySerialzer, ResponseSerialzer
from .models import Survey, Response
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


# This disabled CSRF checks only on the survey API calls.
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class ResponsePermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_anonymous():
            return False

    def has_object_permission(self, request, view, obj):
        return True


class TemplateNameMixin:

    '''
    For the given ViewClass return [viewclass_list.html, viewclass.html]
    as the list of templates to try.
    '''

    def get_template_names(self):
        return ['%s_%s.html' % (self.__class__.__name__.lower(), self.action),
                '%s.html' % self.__class__.__name__.lower()]


class SurveyViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerialzer
    paginate_by = 100


class ResponseViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = Response.objects.all()
    serializer_class = ResponseSerialzer
    paginate_by = 100
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # Eventually replace this naive implementation with a
        # django-restframework-filters + django-filter version that supports
        # JSONField

        data_queries = dict([
            (k, v) for (k, v) in
            self.request.query_params.items()
            if k.startswith('data__')
        ])

        return super().get_queryset().filter(**data_queries)
