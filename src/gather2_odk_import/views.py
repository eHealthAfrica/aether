from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.six.moves import StringIO

from rest_framework import serializers, viewsets

from rest_framework.renderers import BaseRenderer
from rest_framework.generics import ListCreateAPIView

from .models import FormTemplate


class FormTemplateListSerializer(serializers.ListSerializer):
    pass


class FormTemplateSerializer(serializers.ModelSerializer):

    downloadUrl = serializers.URLField(source='get_absolute_url')
    descriptionText = serializers.CharField(source='description')

    class Meta:
        model = FormTemplate
        list_serializer_class = FormTemplateListSerializer
        fields = ('name', 'descriptionText', 'downloadUrl',)
        read_only_fields = fields


class SourceFieldContentSerializer(serializers.ModelSerializer):

    media_type = 'application/xml'
    format = 'xform'

    class Meta:
        model = FormTemplate
        fields = ('source', )
        read_only_fields = fields


class SourceFieldContentRenderer(BaseRenderer):
    media_type = 'application/xml'
    format = 'xform'

    def render(self, data, media_type=None, renderer_context=None):
        return data['source']


class XFormListRenderer(BaseRenderer):

    media_type = 'application/xml'
    format = 'xform'

    def render(self, data, media_type=None, renderer_context=None):

        stream = StringIO()

        xml = SimplerXMLGenerator(stream, 'utf-8')
        xml.startDocument()
        xml.startElement("xforms", {
            'xmlns': 'http://openrosa.org/xforms/xformsList'
        })

        for form in data:
            xml.startElement("xform", {})
            for key, value in form.items():
                xml.addQuickElement(key, value)
            xml.endElement("xform")

        xml.endElement("xforms")
        xml.endDocument()

        return stream.getvalue()


class XFormListView(ListCreateAPIView):
    model = FormTemplate
    queryset = FormTemplate.objects.all()
    serializer_class = FormTemplateSerializer
    renderer_classes = [XFormListRenderer, ] + ListCreateAPIView.renderer_classes


class XFormViewSet(viewsets.ModelViewSet):
    model = FormTemplate
    queryset = FormTemplate.objects.all()
    serializer_class = SourceFieldContentSerializer
    renderer_classes = [SourceFieldContentRenderer, ] + viewsets.ModelViewSet.renderer_classes
