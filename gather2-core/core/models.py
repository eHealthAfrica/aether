#encoding: utf-8
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.core.validators import MaxLengthValidator, MinLengthValidator
import os
import io
import json
import tempfile
import subprocess


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
        import ast
        # TODO: Do not run this if there are no functions to run, also pull this out to it's own function.
        with tempfile.TemporaryDirectory(dir='/tmp/') as tmpdirname:
            print('created temporary directory', tmpdirname)
            with tempfile.NamedTemporaryFile(dir=tmpdirname, suffix='.py') as fp:
                print(fp.name)
                for obj in base_iterator:
                    mapped_data = obj.data
                    if self._decorate_funcs:
                        for fn in self._decorate_funcs:
                            fp.truncate()
                            code = '''
data={mapped_data}

{fn}
'''.format(mapped_data=mapped_data, fn=fn)
                            fp.write(bytes(code, 'UTF-8'))
                            fp.seek(0)
                            raw_mapped_data, raw_err = subprocess.Popen(["pypy-sandbox", "--timeout", "1", "--tmp", tmpdirname, os.path.basename(fp.name)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                ).communicate()
                            err = '\n'.join((raw_err.decode("utf-8")).splitlines()[1:-1]) or None

                            try:
                                if raw_mapped_data:
                                    mapped_data = (ast.literal_eval(raw_mapped_data.decode("utf-8").strip()))
                                else:
                                    mapped_data = None
                            except (ValueError, SyntaxError) as e:
                                print(e, raw_mapped_data)
                                mapped_data = raw_mapped_data.decode("utf-8").strip()
                        obj.mapped_data = mapped_data
                        obj.mapped_err = err

                    else:
                        obj.mapped_data = None

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
