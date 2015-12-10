import factory
from .mock_data import XFORM_XML


class XFormFactory(factory.django.DjangoModelFactory):

    """
    factory for creating xforms using valid xml data
    """

    class Meta:
        model = 'api.XForm'

    xml_data = XFORM_XML
