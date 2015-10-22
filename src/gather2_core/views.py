from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from .serializers import SurveySerialzer, SurveyItemSerialzer
from .models import Survey, SurveyItem
from rest_framework import permissions


class SurveyPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True


class SurveyItemPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_anonymous():
            return False

        survey_id = view.kwargs.get('parent_lookup_survey', "-1")
        survey = Survey.objects.filter(id=int(survey_id), created_by=request.user).exists()
        return survey

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
    queryset = Survey.objects.all()
    serializer_class = SurveySerialzer
    paginate_by = 100
    permission_classes = (SurveyPermissions,)


class SurveyItemViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = SurveyItem.objects.all()
    serializer_class = SurveyItemSerialzer
    paginate_by = 100
    permission_classes = (SurveyItemPermissions,)

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
