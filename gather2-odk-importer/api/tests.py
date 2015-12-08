from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from mock import patch

from .models import XForm
from .mock_data import XFORM_XML
from .auth_utils import AuthService
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
        self.assertTrue("<formID>%s</formID>" % self.xform1.pk in response.content)
        self.assertTrue("<formID>%s</formID>" % self.xform2.pk not in response.content)
        self.assertTrue("<formID>%s</formID>" % self.xform3.pk not in response.content)

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

    def test_create_xform(self):
        xform_file = SimpleUploadedFile(
            "text.xml",
            XFORM_XML,
            content_type="text/xml"
        )

        arg_dict = {}
        arg_dict['username'] = 'test_user3'
        arg_dict['title'] = 'new form'
        arg_dict['description'] = 'form description'
        arg_dict['xml_file'] = xform_file

        response = self.c.post('/test_user3/forms/create', arg_dict)
        # redirect after form is submitted
        self.assertEqual(response.status_code, 302)

    def test_failed_auth_listview(self):
        with patch.object(AuthService, 'authorise', return_value=False):
            response = self.c.get('/test_user/formList')
            self.assertEqual(response.status_code, 401)

    def test_failed_auth_createview(self):
        with patch.object(AuthService, 'authorise', return_value=False):
            xform_file = SimpleUploadedFile(
                "text.xml",
                XFORM_XML,
                content_type="text/xml"
            )

            arg_dict = {}
            arg_dict['title'] = 'new form'
            arg_dict['description'] = 'form description'
            arg_dict['xml_file'] = xform_file

            response = self.c.post('/test_user3/forms/create', arg_dict)
            self.assertEqual(response.status_code, 401)

    def test_get_manifest(self):
        # TODO this is a stubbed test as the manifest is always empty currently
        response = self.c.get('/test_user/xformsManifest/%s' % self.xform1.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_xform_create_form_view(self):
        response = self.c.get('/test_user/forms/create')
        self.assertEqual(response.status_code, 200)

    def test_failed_auth_xform_create_form_view(self):
        with patch.object(AuthService, 'authorise', return_value=False):
            response = self.c.get('/test_user/forms/create')
            self.assertEqual(response.status_code, 401)

    def test_xform_xml_view(self):
        response = self.c.get('/test_user/forms/%s/form.xml' % self.xform1.pk)
        self.assertEqual(response.status_code, 200)

    def test_failed_auth_xform_xml_view(self):
        with patch.object(AuthService, 'authorise', return_value=False):
            response = self.c.get('/test_user/forms/%s/form.xml' % self.xform1.pk)
            self.assertEqual(response.status_code, 401)
