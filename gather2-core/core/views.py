from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from .serializers import SurveySerialzer, SurveyItemSerialzer
from .models import Survey, SurveyItem


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


class SurveyItemViewSet(TemplateNameMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = SurveyItem.objects.all()
    serializer_class = SurveyItemSerialzer
    paginate_by = 100
