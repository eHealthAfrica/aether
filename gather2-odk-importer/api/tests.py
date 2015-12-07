from django.test import TestCase, Client
from .models import XForm
from .test_factories import XFormFactory


class XFormAPITestCase(TestCase):

    """
    Positive test cases for XForm API
    """

    # TODO will need to add basic auth password when auth is done

    def setUp(self):
        self.c = Client()
        self.xform1 = XFormFactory(username="test_user")
        self.xform2 = XFormFactory(username="test_user2")
        self.xform3 = XFormFactory(username="test_user2")

    def test_fetch_xforms(self):
        """
        test that fetching a list of forms returns a 200 response
        """
        response = self.c.get('/test_user/formList')
        self.assertEqual(response.status_code, 200)

    def test_number_of_forms(self):
        """
        test that only forms for the chosen user are returned
        """
        forms = XForm.objects.filter(username="test_user")
        self.assertEqual(forms.count(), 1)

        for form in forms:
            self.assertEqual(form.username, "test_user")

        forms = XForm.objects.filter(username="test_user2")
        self.assertEqual(forms.count(), 2)

        for form in forms:
            self.assertEqual(form.username, "test_user2")
