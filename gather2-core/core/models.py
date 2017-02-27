# encoding: utf-8
import ast
import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

logger = logging.getLogger(__name__)


class Attachment(models.Model):
    attachment_file = models.FileField('attachment')
    response = models.ForeignKey('Response', related_name='attachments')
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True, db_index=True)


class Survey(models.Model):
    name = models.CharField(max_length=50)
    # TODO: Make this readonly
    schema = JSONField(blank=False, null=False, default="{}")
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('survey-detail', args=[str(self.id)])


class Response(models.Model):
    survey = models.ForeignKey(Survey)
    data = JSONField(blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)


class MapFunction(models.Model):
    code = models.TextField()
    survey = models.ForeignKey(Survey)
    created = models.DateTimeField(auto_now_add=True, db_index=True)


class MapResult(models.Model):
    map_function = models.ForeignKey(MapFunction)
    response = models.ForeignKey(Response)
    output = JSONField(blank=True, null=False, default="{}", editable=False)
    error = models.TextField(editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)


class ReduceFunction(models.Model):
    code = models.TextField()
    output = JSONField(blank=False, null=False, default="{}", editable=False)
    error = models.TextField(blank=True, default="", editable=False)
    map_function = models.ForeignKey(MapFunction)
    created = models.DateTimeField(auto_now_add=True, db_index=True)


def calculate(code, data):
    """
    This takes some python2 code and the data to be applied to it. Returns
    python literals as a list or the raw output.
    """
    # TODO: dont hardcode the tmp dir
    # TODO: Set up a ramdisk in tmp and use that
    out = []
    with tempfile.TemporaryDirectory(dir='/tmp/') as tmpdirname:
        logger.info('created temporary directory', tmpdirname)
        with tempfile.NamedTemporaryFile(dir=tmpdirname, suffix='.py') as fp:
            # Maybe this should be moved to use stdin in the `communicate`
            # and not written to file.
            sandbox_code = '''
data={data}

{code}
'''.format(data=data, code=code)
            # Write the sandbox code to the tmp file
            fp.write(bytes(sandbox_code, 'UTF-8'))
            # Go back to the beginning so, this may not be needed
            fp.seek(0)
            # Run the code in the sandbox
            raw_out, raw_err = subprocess.Popen(["pypy-sandbox", "--timeout", "5", "--tmp", tmpdirname, os.path.basename(fp.name)],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE
                                                ).communicate()
            # Strip off the "site" import error
            err = '\n'.join(
                (raw_err.decode("utf-8")).splitlines()[1:]) or None

            try:
                if raw_out:
                    # See if what was returned was a python literal, this is
                    # safe
                    for line in raw_out.decode("utf-8").splitlines():
                        out.append(ast.literal_eval(line.strip()))
                else:
                    out.append(None)
            except (ValueError, SyntaxError) as e:
                logger.info(e)
                out.append(raw_out.decode("utf-8").strip())
    return out, err
