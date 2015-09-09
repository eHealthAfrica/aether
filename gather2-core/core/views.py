from django.shortcuts import render
from rest_framework import viewsets

from .serializers import SurveySerialzer, SurveyItemSerialzer
from .models import Survey, SurveyItem


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerialzer
    paginate_by = 100


class SurveyItemViewSet(viewsets.ModelViewSet):
    queryset = SurveyItem.objects.all()
    serializer_class = SurveyItemSerialzer
    paginate_by = 100
