from django.db import models
from django.utils import timezone


class XForm(models.Model):

    """
    database representation of an XForm

    The data is stored in XML format and converted to the other supported
    formats when it is needed
    """

    # Users can only see their forms, auth is done by core so store the
    # username as a field on the model
    username = models.CharField(
        max_length=100
    )

    name = models.CharField(
        max_length=100
    )

    xml_data = models.TextField()

    created_at = models.DateTimeField(
        default=timezone.now
    )
