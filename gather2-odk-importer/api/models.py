import xmltodict

from hashlib import md5

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.utils import timezone

from . import core_utils


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


def get_xml_title(data):
    '''
    Extracts form title from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <instance>
                <None id="F O R M I D"></None>
              </instance>
              <instance id="1"></instance>
              <instance id="2"></instance>

              <instance id="n"></instance>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>
     '''
    try:
        return data['h:html']['h:head']['h:title']
    except:
        return None


def get_xml_form_id(data):
    '''
    Extracts form id from xml definition

        <h:html>
          <h:head>
            <h:title> T I T L E </h:title>
            <model>
              <instance>
                <None id="F O R M I D"></None>
              </instance>
              <instance id="1"></instance>
              <instance id="2"></instance>

              <instance id="n"></instance>
            </model>
          </h:head>
          <h:body>
          </h:body>
        </h:html>
    '''
    try:
        instance = data['h:html']['h:head']['model']['instance']
        # this can be a list of intances or one entry
        try:
            return instance['None']['@id']
        except:
            # assumption: the first one is the form definition, the rest are the choices
            return instance[0]['None']['@id']
    except:
        pass

    return None


def validate_xmldict(value):
    '''
    Validates xml definition:

    1. parses xml
    2. checks if title is valid
    3. checks if form id is valid
    '''
    try:
        data = xmltodict.parse(value)

        if not get_xml_title(data):
            raise ValidationError('missing title')
        if not get_xml_form_id(data):
            raise ValidationError('missing form_id')

    except Exception as e:
        raise ValidationError(e)


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

    description = models.TextField(default='', null=True)
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
