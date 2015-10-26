from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.six.moves import StringIO

from rest_framework import serializers

from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework.renderers import BaseRenderer
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import FormTemplate


class FormTemplateSerializer(serializers.ModelSerializer):

    downloadUrl = serializers.URLField(source='get_absolute_url')
    descriptionText = serializers.CharField(source='description')
    formID = serializers.CharField(source='id')

    class Meta:
        model = FormTemplate
        fields = ('formID', 'name', 'descriptionText', 'downloadUrl', 'source')
        read_only_fields = fields


class XFormListRenderer(BaseRenderer):

    media_type = 'text/xml'
    format = 'xform'

    def render(self, data, media_type=None, renderer_context=None):

        if type(data) is ReturnDict:
            return data['source']

        stream = StringIO()

        xml = SimplerXMLGenerator(stream, 'utf-8')
        xml.startDocument()
        xml.startElement("xforms", {
            'xmlns': 'http://openrosa.org/xforms/xformsList'
        })

        for form in data:
            xml.startElement("xform", {})
            for key, value in form.items():
                if key != 'source':
                    xml.addQuickElement(key, value)
            xml.endElement("xform")

        xml.endElement("xforms")
        xml.endDocument()

        return stream.getvalue()


class XFormViewSet(ReadOnlyModelViewSet):
    model = FormTemplate
    queryset = FormTemplate.objects.all()
    serializer_class = FormTemplateSerializer
    renderer_classes = [XFormListRenderer, ]  # + ReadOnlyModelViewSet.renderer_classes

    def _add_openrosa_headers(self, response):
        response['X-OpenRosa-Accept-Content-Length'] = '10000000'
        response['X-OpenRosa-Version'] = '1.0'
        return response

    def list(self, *args, **kwargs):
        return self._add_openrosa_headers(super().list(self, *args, **kwargs))

    def retrieve(self, *args, **kwargs):
        return self._add_openrosa_headers(super().retrieve(self, *args, **kwargs))
