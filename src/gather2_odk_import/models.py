from django.db import models

# Create your models here.
from django.conf import settings
from rest_framework.reverse import reverse


class FormTemplate(models.Model):

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)

    name = models.CharField(max_length=100, blank=False)
    description = models.CharField(max_length=200, blank=True)

    source = models.TextField(blank=False)

    def get_absolute_url(self):
        return reverse("formtemplate-detail", args=[str(self.id)])

    def __str__(self):
        return '%s - %s' % (self.id, self.name)
