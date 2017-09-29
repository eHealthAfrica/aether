import xmltodict

from hashlib import md5

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.utils import timezone

from . import core_utils
from .xform_utils import get_xml_title, get_xml_form_id, validate_xmldict


class Survey(models.Model):
    '''
    Database link of a Gather2 Core Survey

    The needed and common data is stored here, like the list of granted surveyors.
    '''

    # This is needed to submit data to core
    # (there is a one to one relation)
    survey_id = models.IntegerField(primary_key=True)

    name = models.TextField(null=True, blank=True, default='')

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), related_name='surveys', blank=True)

    @property
    def gather_core_url(self):
        return core_utils.get_survey_responses_url(survey_id=self.pk)

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the Survey.

        Rules:
        - User is superuser.
        - Survey has no surveyors.
        - User is in the surveyors list.
        '''
        return (
            user.is_superuser or
            self.surveyors.count() == 0 or
            user in self.surveyors.all()
        )

    def __str__(self):  # pragma: no cover
        return '{} - {}'.format(str(self.survey_id), self.name)


class XForm(models.Model):
    '''
    Database representation of an XForm

    The data is stored in XML format and converted to the other supported
    formats when it is needed
    '''

    # taken from xml_data
    title = models.TextField(default='', editable=False)
    form_id = models.TextField(default='', editable=False, null=False)

    # here comes the extracted data from an xForm file
    xml_data = models.TextField(blank=True, validators=[validate_xmldict])

    description = models.TextField(default='', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # This is needed to submit data to core
    survey = models.ForeignKey(
        Survey,
        related_name='xforms',
        null=False,
        blank=False,
    )

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), related_name='xforms', blank=True)

    @property
    def gather_core_url(self):
        return self.survey.gather_core_url

    @property
    def hash(self):
        return u'%s' % md5(self.xml_data.encode('utf8')).hexdigest()

    @property
    def id_string(self):
        return str(self.pk)

    @property
    def url(self):
        return reverse('xform-get-xml_data', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        try:
            validate_xmldict(self.xml_data)
        except:
            raise IntegrityError('xml_data not valid')

        data = xmltodict.parse(self.xml_data)
        self.title = get_xml_title(data)
        self.form_id = get_xml_form_id(data)
        return super(XForm, self).save(*args, **kwargs)

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the xForm.

        Rules:
        - User is superuser.
        - xForm and Survey have no surveyors.
        - User is in the xForm or Survey surveyors list.
        '''
        return (
            user.is_superuser or
            (self.surveyors.count() == 0 and self.survey.surveyors.count() == 0) or
            user in self.surveyors.all() or
            user in self.survey.surveyors.all()
        )

    def __str__(self):  # pragma: no cover
        return '{} - {}'.format(str(self.title), self.form_id)
