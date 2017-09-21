from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from . import CustomTestCase
from ..serializers import SurveyorSerializer, XFormSerializer


class SerializersTests(CustomTestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()
        self.request = RequestFactory().get('/')

    def test_xform_serializer__no_files(self):
        xform = XFormSerializer(
            data={
                'gather_core_survey_id': 1,
                'description': 'test xml data',
                'xml_data': self.samples['xform']['raw-xml'],
                'surveyors': [],
            },
            context={'request': self.request},
        )
        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_xml_file(self):
        with open(self.samples['xform']['file-xml'], 'rb') as data:
            file = SimpleUploadedFile('xform.xml', data.read())

        xform = XFormSerializer(
            data={
                'gather_core_survey_id': 1,
                'description': 'test xml file',
                'xml_file': file,
                'surveyors': [],
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_xform_serializer__with_xls_file(self):
        with open(self.samples['xform']['file-xls'], 'rb') as data:
            file = SimpleUploadedFile('xform.xls', data.read())

        xform = XFormSerializer(
            data={
                'gather_core_survey_id': 1,
                'description': 'test xls file',
                'xls_file': file,
                'surveyors': [],
            },
            context={'request': self.request},
        )

        self.assertTrue(xform.is_valid(), xform.errors)
        xform.save()
        self.assertEqual(xform.data['form_id'], 'my-test-form')
        self.assertEqual(xform.data['title'], 'my-test-form')
        self.assertIn('<h:head>', xform.data['xml_data'])

    def test_surveyor_serializer__empty_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '',
            },
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__password_eq_username(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': 'test',
            },
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__short_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '0123456',
            },
        )
        self.assertFalse(user.is_valid(), user.errors)

    def test_surveyor_serializer__strong_password(self):
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': '~t]:vS3Q>e{2k]CE',
            },
        )
        self.assertTrue(user.is_valid(), user.errors)

    def test_surveyor_serializer__create_and_update(self):
        password = '~t]:vS3Q>e{2k]CE'
        user = SurveyorSerializer(
            data={
                'username': 'test',
                'password': password,
            },
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        user_obj = get_user_model().objects.get(pk=user.data['id'])

        self.assertNotEqual(user.data['password'], password, 'no raw password')
        self.assertIn(self.surveyor_group, user_obj.groups.all(), 'has the group "surveyor"')

        updated_user = SurveyorSerializer(
            user_obj,
            data={
                'username': 'test',
                'password': 'wUCK:CQsUd?)Zr93',
            },
        )

        self.assertTrue(updated_user.is_valid(), updated_user.errors)
        updated_user.save()
        updated_user_obj = get_user_model().objects.get(pk=updated_user.data['id'])

        self.assertNotEqual(updated_user.data['password'], user.data['password'])
        self.assertIn(self.surveyor_group, updated_user_obj.groups.all())

        # update with the hashed password does not change the password
        updated_user_2 = SurveyorSerializer(
            updated_user_obj,
            data={
                'username': 'test2',
                'password': updated_user.data['password']
            },
        )

        self.assertTrue(updated_user_2.is_valid(), updated_user_2.errors)
        updated_user_2.save()
        updated_user_2_obj = get_user_model().objects.get(pk=updated_user_2.data['id'])

        self.assertEqual(updated_user_2.data['username'], 'test2')
        self.assertEqual(updated_user_2.data['password'], updated_user.data['password'])
        self.assertIn(self.surveyor_group, updated_user_2_obj.groups.all())
