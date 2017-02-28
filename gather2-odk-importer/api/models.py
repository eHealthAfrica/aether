from hashlib import md5
from django.conf import settings

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

import xmltodict


def validate_xmldict(value):
    try:
        xmltodict.parse(value)
        assert ['h:html']['h:head']['h:title'], 'missing "title" in xlsform or XForm'
    except Exception as e:
        raise ValidationError(e)


class XForm(models.Model):

    """
    database representation of an XForm
    The data is stored in XML format and converted to the other supported
    formats when it is needed
    """

    title = models.CharField(default='', max_length=64, editable=False, unique=True)
    xml_data = models.TextField(blank=True, validators=[validate_xmldict])
    description = models.TextField(default=u'', null=True)
    created_at = models.DateTimeField(default=timezone.now)
    gather_core_survey_id = models.IntegerField()

    @property
    def gather_core_url(self):
        return settings.GATHER_CORE_URL + '/surveys/{survey_id}/responses/'.format(survey_id=self.gather_core_survey_id)

    @property
    def hash(self):
        return u'%s' % md5(self.xml_data.encode('utf8')).hexdigest()

    @property
    def id_string(self):
        return str(self.pk)

    @property
    def url(self):
        return reverse("download_xform", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        try:
            d = xmltodict.parse(self.xml_data)
            self.title = d['h:html']['h:head']['h:title']  # TODO: make this more robust
            self.form_id = d['h:html']['h:head']['model']['instance']['None']['@id']
        except Exception as e:
            print(e)

        return super(XForm, self).save(*args, **kwargs)
