import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from . import CustomTestCase
from ..models import Mapping, XForm, MediaFile


class ModelsTests(CustomTestCase):

    MAPPING_ID = uuid.uuid4()

    def test__xform__create__raises_errors(self):
        # missing required fields
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
        )
        # missing xml_data
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            mapping=self.helper_create_mapping(),
        )
        # missing mapping id
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            xml_data=self.samples['xform']['xml-ok'],
        )
        # xml_data with missing properties
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            mapping=self.helper_create_mapping(),
            xml_data='''
                <h:html>
                  <h:head>
                    <model>
                      <instance>
                      </instance>
                    </model>
                  </h:head>
                  <h:body>
                  </h:body>
                </h:html>
            ''',
        )
        # corrupted xml_data
        self.assertRaises(
            IntegrityError,
            XForm.objects.create,
            mapping=self.helper_create_mapping(),
            xml_data='''
                <h:html
                    xmlns="http://www.w3.org/2002/xforms"
                    xmlns:ev="http://www.w3.org/2001/xml-events"
                    xmlns:h="http://www.w3.org/1999/xhtml"
                    xmlns:jr="http://openrosa.org/javarosa"
                    xmlns:orx="http://openrosa.org/xforms"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema">

                  <h:head>
            ''',
        )

    def test__xform__save(self):
        instance = XForm.objects.create(
            mapping=self.helper_create_mapping(mapping_id=self.MAPPING_ID),
            xml_data=self.samples['xform']['xml-ok'],
        )

        self.assertEqual(instance.form_id, 'xform-id-test')
        self.assertEqual(instance.title, 'xForm - Test')
        self.assertEqual(instance.version, 'v1')
        self.assertEqual(instance.download_url,
                         '/forms/{}/form.xml?version=v1'.format(instance.pk))
        self.assertEqual(instance.manifest_url, '', 'without media files no manifest url')
        self.assertEqual(str(instance), 'xForm - Test - xform-id-test')

    def test__mapping__surveyors(self):
        instance = Mapping.objects.create(
            mapping_id=self.MAPPING_ID,
        )
        self.assertEqual(instance.surveyors.count(), 0, 'no granted surveyors')

        self.helper_create_superuser()
        self.assertTrue(instance.is_surveyor(self.admin),
                        'superusers are always granted surveyors')

        self.helper_create_user()
        self.assertTrue(instance.is_surveyor(self.user),
                        'if not granted surveyors all users are surveyors')

        surveyor = self.helper_create_surveyor()
        instance.surveyors.add(surveyor)
        instance.save()

        self.assertEqual(instance.surveyors.count(), 1, 'one granted surveyor')
        self.assertTrue(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(self.admin),
                        'superusers are always granted surveyors')
        self.assertFalse(instance.is_surveyor(self.user),
                         'if granted surveyors not all users are surveyors')

    def test__xform__surveyors(self):
        instance = XForm.objects.create(
            mapping=self.helper_create_mapping(mapping_id=self.MAPPING_ID),
            xml_data=self.samples['xform']['xml-ok'],
        )
        self.assertEqual(instance.surveyors.count(), 0, 'no granted surveyors')

        self.helper_create_superuser()
        self.assertTrue(instance.is_surveyor(self.admin),
                        'superusers are always granted surveyors')

        self.helper_create_user()
        self.assertTrue(instance.is_surveyor(self.user),
                        'if not granted surveyors all users are surveyors')

        surveyor = self.helper_create_surveyor(username='surveyor')
        instance.surveyors.add(surveyor)
        instance.save()

        self.assertEqual(instance.surveyors.count(), 1, 'one custom granted surveyor')
        self.assertTrue(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(self.admin),
                        'superusers are always granted surveyors')
        self.assertFalse(instance.is_surveyor(self.user),
                         'if granted surveyors not all users are surveyors')

        surveyor2 = self.helper_create_surveyor(username='surveyor2')
        instance.mapping.surveyors.add(surveyor2)
        instance.mapping.save()
        self.assertEqual(instance.surveyors.count(), 1, 'one custom granted surveyor')
        self.assertTrue(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(surveyor2),
                        'mapping surveyors are also xform surveyors')

        instance.surveyors.clear()
        instance.save()
        self.assertEqual(instance.surveyors.count(), 0, 'no custom granted surveyor')
        self.assertFalse(instance.is_surveyor(surveyor))
        self.assertTrue(instance.is_surveyor(surveyor2),
                        'mapping surveyors are always xform surveyors')

    def test__xform__media(self):
        xform = XForm.objects.create(
            mapping=self.helper_create_mapping(mapping_id=self.MAPPING_ID),
            xml_data=self.samples['xform']['xml-ok'],
        )

        media = MediaFile.objects.create(
            xform=xform,
            media_file=SimpleUploadedFile('sample.txt', b'abc'),
        )
        self.assertEqual(media.name, 'sample.txt', 'takes file name')
        self.assertEqual(media.md5sum, '900150983cd24fb0d6963f7d28e17f72')
        self.assertEqual(str(media), 'xForm - Test - xform-id-test - sample.txt')

        media.media_file = SimpleUploadedFile('sample2.txt', b'abcd')
        media.save()
        self.assertEqual(media.name, 'sample.txt', 'no replaces name')
        self.assertEqual(media.md5sum, 'e2fc714c4727ee9395f324cd2e7f331f')
        # with media files there is manifest_url
        self.assertEqual(xform.manifest_url,
                         '/forms/{}/manifest.xml?version={}'.format(xform.id, xform.version))

    def test__xform__version(self):
        xform = XForm.objects.create(
            mapping=self.helper_create_mapping(mapping_id=self.MAPPING_ID),
            xml_data=self.samples['xform']['xml-ok'],
        )
        last_version = xform.version
        self.assertEqual(last_version, 'v1')

        xform.xml_data = self.samples['xform']['xml-ok']
        xform.save()
        self.assertEqual(last_version, xform.version, 'nothing changed')
        last_version = xform.version

        xform.xml_data = self.samples['xform']['raw-xml']
        xform.save()
        self.assertNotEqual(last_version, xform.version, 'changed xml data')
