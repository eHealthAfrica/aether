from django.test import TestCase, Client
from .test_factories import XFormFactory


class XFormAPITestCase(TestCase):

    """
    Positive test cases for XForm API
    """

    def setUp(self):
        self.c = Client()
        self.xform = XFormFactory(username="test_user")

    def test_fetch_xforms(self):
        # TODO will need to add basic auth password when auth is done
        response = self.c.get('/test_user/formList')
        self.assertEqual(response.status_code, 200)
