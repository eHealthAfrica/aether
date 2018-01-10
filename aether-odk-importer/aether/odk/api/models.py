import xmltodict
import uuid

from hashlib import md5

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import models, IntegrityError
from django.utils import timezone

from .xform_utils import get_xml_title, get_xml_form_id, get_xml_version, validate_xmldict


class Mapping(models.Model):
    '''
    Database link of a Aether Kernel Mapping

    The needed and common data is stored here, like the list of granted surveyors.

    '''

    # This is needed to submit data to kernel
    # (there is a one to one relation)
    mapping_id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    name = models.TextField(null=True, blank=True, default='')

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), blank=True)

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the Mapping.

        Rules:
            - User is superuser.
            - Mapping has no surveyors.
            - User is in the surveyors list.

        '''

        return (
            user.is_superuser or
            self.surveyors.count() == 0 or
            user in self.surveyors.all()
        )

    def __str__(self):
        return '{} - {}'.format(str(self.mapping_id), self.name)

    class Meta:
        app_label = 'odk'
        default_related_name = 'mappings'
        ordering = ['name']


class XForm(models.Model):
    '''
    Database representation of an XForm

    The data is stored in XML format and could be converted to the
    other supported formats when it is needed.

    '''

    # This is needed to submit data to kernel
    mapping = models.ForeignKey(to=Mapping, on_delete=models.CASCADE)

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), blank=True)

    # here comes the extracted data from an xForm file
    xml_data = models.TextField(blank=True, validators=[validate_xmldict])

    # taken from xml_data
    title = models.TextField(default='', editable=False)
    form_id = models.TextField(default='', editable=False)
    version = models.TextField(default='0', blank=True)
    md5sum = models.CharField(default='', editable=False, max_length=36)

    description = models.TextField(default='', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

    @property
    def download_url(self):
        '''
        https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

        Represents the `<downloadUrl/>` entry in the forms list.

        '''

        return '{url}?version={version}'.format(
            url=reverse('xform-get-download', kwargs={'pk': self.pk}),
            version=self.version,
        )

    @property
    def manifest_url(self):
        '''
        https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

        Represents the `<manifestUrl/>` entry in the forms list.

        '''

        if self.media_files.count() > 0:
            return '{url}?version={version}'.format(
                url=reverse('xform-get-manifest', kwargs={'pk': self.pk}),
                version=self.version,
            )
        else:
            return ''

    def save(self, *args, **kwargs):
        try:
            validate_xmldict(self.xml_data)
        except ValidationError as ve:
            raise IntegrityError('xml_data not valid')

        data = xmltodict.parse(self.xml_data)
        self.title = get_xml_title(data)
        self.form_id = get_xml_form_id(data)

        version = get_xml_version(data)
        if version:
            # set version from xml data
            self.version = version

        self.update_hash(increase_version=version is None)

        return super(XForm, self).save(*args, **kwargs)

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the xForm.

        Rules:
            - User is superuser.
            - xForm and Mapping have no surveyors.
            - User is in the xForm or Mapping surveyors list.

        '''

        return (
            user.is_superuser or
            (self.surveyors.count() == 0 and self.mapping.surveyors.count() == 0) or
            user in self.surveyors.all() or
            user in self.mapping.surveyors.all()
        )

    def update_hash(self, increase_version=False):
        md5sum = md5(self.xml_data.encode('utf8')).hexdigest()
        if md5sum != self.md5sum and increase_version:
            self.increase_version()
        self.md5sum = md5sum

    def increase_version(self):
        self.version = '{:%Y%m%d%H}'.format(timezone.now())

    def __str__(self):
        return '{} - {}'.format(str(self.title), self.form_id)

    class Meta:
        app_label = 'odk'
        default_related_name = 'xforms'
        ordering = ['title', 'form_id']


def __media_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<mapping>/<xform>/filename
    return '{mapping}/{xform}/{filename}'.format(
        mapping=instance.xform.mapping.pk,
        xform=instance.xform.pk,
        filename=filename,
    )


class MediaFile(models.Model):
    '''
    Database representation of a media file linked to an XForm

    '''

    xform = models.ForeignKey(to=XForm, on_delete=models.CASCADE)

    name = models.TextField(blank=True)
    media_file = models.FileField(upload_to=__media_path__)
    md5sum = models.CharField(editable=False, max_length=36)

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

    def save(self, *args, **kwargs):
        # calculate hash
        md5hash = md5()
        for chunk in self.media_file.chunks():
            md5hash.update(chunk)
        self.md5sum = md5hash.hexdigest()

        # assign name if missing
        if not self.name:
            self.name = self.media_file.name

        super(MediaFile, self).save(*args, **kwargs)

    def __str__(self):
        return '{} - {}'.format(str(self.xform), self.name)

    class Meta:
        app_label = 'odk'
        default_related_name = 'media_files'
        ordering = ['xform', 'name']
