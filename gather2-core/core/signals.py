import ast
import logging
import os
import subprocess
import tempfile

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import MapFunction, MapResult, ReduceFunction, Response

logger = logging.getLogger(__name__)

SANDBOX_TEMPLATE = '''
data={data}

{code}
'''


@receiver(post_save, sender=Response, dispatch_uid='response_save')
def response_saved(sender, instance, **kwargs):
    response = instance

    for map_function in response.survey.map_functions.all():
        # Calculate the new output
        outputs, error = calculate(code=map_function.code, data=response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for output in outputs:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=output or '',
                error=error or '',
            )

        for reduce_function in map_function.reduce_functions.all():
            out, err = calculate(
                code=reduce_function.code,
                data=map_function.map_results.all().values_list('output', flat=True),
            )
            reduce_function.output = out
            reduce_function.error = err or ''
            reduce_function.save()


@receiver(post_save, sender=MapFunction, dispatch_uid='map_function_save')
def map_function_saved(sender, instance, **kwargs):
    map_function = instance

    for response in map_function.survey.responses.all():
        # Calculate the new results
        outputs, err = calculate(code=map_function.code, data=response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for output in outputs:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=output or '',
                error=err or '')

    for reduce_function in map_function.reduce_functions.all():
        out, err = calculate(
            code=reduce_function.code,
            data=map_function.map_results.all().values_list('output', flat=True),
        )
        reduce_function.output = out
        reduce_function.error = err or ''
        reduce_function.save()


@receiver(pre_save, sender=ReduceFunction, dispatch_uid='reduce_function_save')
def reduce_function_saved(sender, instance, **kwargs):
    reduce_function = instance
    outputs, error = calculate(
        code=reduce_function.code,
        data=list(
            reduce_function.map_function.map_results.all().values_list('output', flat=True)
        ),
    )
    reduce_function.output = outputs
    reduce_function.error = error or ''


def calculate(code, data):
    '''
    This takes some python2 code and the data to be applied to it. Returns
    python literals as a list or the raw output.
    '''

    # TODO: dont hardcode the tmp dir
    # TODO: Set up a ramdisk in tmp and use that
    out = []
    with tempfile.TemporaryDirectory(dir='/tmp/') as tmpdirname:
        logger.info('created temporary directory', tmpdirname)
        with tempfile.NamedTemporaryFile(dir=tmpdirname, suffix='.py') as fp:
            # Maybe this should be moved to use stdin in the `communicate`
            # and not written to file.
            sandbox_code = SANDBOX_TEMPLATE.format(data=data, code=code)

            # Write the sandbox code to the tmp file
            fp.write(bytes(sandbox_code, 'UTF-8'))
            # Go back to the beginning so, this may not be needed
            fp.seek(0)
            # Run the code in the sandbox
            raw_out, raw_err = subprocess.Popen(
                ['pypy-sandbox', '--timeout', '5', '--tmp', tmpdirname, os.path.basename(fp.name)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()

            # Strip off the "site" import error
            err = '\n'.join((raw_err.decode('UTF-8')).splitlines()[1:]) or None

            try:
                if raw_out:
                    # See if what was returned was a python literal, this is safe
                    for line in raw_out.decode('UTF-8').splitlines():
                        out.append(ast.literal_eval(line.strip()))
                else:
                    out.append(None)
            except (ValueError, SyntaxError) as e:
                out.append(raw_out.decode('UTF-8').strip())

    return out, err
