from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict


# Based on django-queryset-transform.
# This object however, operates on a per-object instance,
# so it doesn't break the result generators


class DecoratingQuerySet(QuerySet):

    """
    An enhancement of the QuerySet which allows objects to be decorated
    with extra properties before they are returned.
    """

    def __init__(self, *args, **kwargs):
        super(DecoratingQuerySet, self).__init__(*args, **kwargs)
        self._decorate_funcs = []

    def _clone(self, **kw):
        c = super(DecoratingQuerySet, self)._clone(**kw)
        c._decorate_funcs = self._decorate_funcs[:]
        return c

    def decorate(self, fn):
        """
        Register a function which will decorate a retrieved object before it's returned.
        """
        if fn not in self._decorate_funcs:
            self._decorate_funcs.append(fn)
        return self

    def iterator(self):
        """
        Overwritten iterator which will apply the decorate functions before returning it.
        """
        base_iterator = super(DecoratingQuerySet, self).iterator()

        for obj in base_iterator:
            mapped_data = model_to_dict(obj)
            # Apply the decorators
            for fn in self._decorate_funcs:
                mapped_data = fn(mapped_data)
            obj.mapped_data = mapped_data
            yield obj


class DecoratorManager(models.Manager):

    """
    The manager class which ensures the enhanced DecoratorQuerySet object is used.
    """

    def get_queryset(self):
        return DecoratingQuerySet(self.model)


class Survey(models.Model):
    name = models.CharField(max_length=15)
    schema = JSONField(blank=False, null=False, default="{}")
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)

    def __str__(self):
        return '%s - %s' % (self.id, self.name)


class Response(models.Model):
    objects = DecoratorManager()
    survey = models.ForeignKey(Survey)
    data = JSONField(blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)


class Map(models.Model):
    code = models.TextField()
    survey = models.ForeignKey(Survey)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
