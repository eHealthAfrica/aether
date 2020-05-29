# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from datetime import datetime
import csv
import json
import logging
import math
import os
import re
import shutil
import tempfile
import time
import zipfile

from multiprocessing import Process, Value
from openpyxl import Workbook

from django.conf import settings
from django.core.files import File
from django.db import connection, transaction
from django.db.models import Count, F
from django.utils.translation import gettext as _

from rest_framework.response import Response
from rest_framework.decorators import action

from aether.python.avro.tools import ARRAY_PATH, MAP_PATH, UNION_PATH, extract_jsonpaths_and_docs
from aether.python.entity.extractor import ENTITY_EXTRACTION_ENRICHMENT, ENTITY_EXTRACTION_ERRORS

from .models import Attachment, ExportTask, ExportTaskFile

RE_CONTAINS_DIGIT = re.compile(r'\.\d+\.')  # a.999.b
RE_ENDSWITH_DIGIT = re.compile(r'\.\d+$')   # a.b.999

CSV_FORMAT = 'csv'
XLSX_FORMAT = 'xlsx'

# Total number of rows on a worksheet (since Excel 2007): 1048576
# https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3
MAX_SIZE = 1048574  # the missing ones are the header ones (paths & labels)
RECORDS_PAGE_SIZE = 1000
ATTACHMENTS_PAGE_SIZE = 200

# Nowadays the ZIP file size limit is 16 EB (exabytes), but
# 4 GB (gigabytes) size is a limitation for an old zip format and,
# it is a limit for any file on FAT32 disks.
MAX_FILE_SIZE = 4 * 1000 * 1000 * 1000  # 4 GB

# CSV Dialect
# https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
DEFAULT_DIALECT = 'aether_dialect'
csv.register_dialect(
    DEFAULT_DIALECT,
    delimiter=settings.EXPORT_CSV_SEPARATOR,
    doublequote=False,
    escapechar=settings.EXPORT_CSV_ESCAPE,
    quotechar=settings.EXPORT_CSV_QUOTE,
    quoting=csv.QUOTE_NONNUMERIC,
)

DEFAULT_OPTIONS = {
    'header_content': settings.EXPORT_HEADER_CONTENT,
    'header_separator': settings.EXPORT_HEADER_SEPARATOR,
    'header_shorten': settings.EXPORT_HEADER_SHORTEN,
    'data_format': settings.EXPORT_DATA_FORMAT,
}

EXPORT_FIELD_ID = 'id'
EXPORT_FIELD_DATA = 'exporter_data'
EXPORT_FIELD_ATTACHMENT = 'exporter_attachment'

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExporterMixin():
    '''
    ModelViewSet that includes export endpoints ``xlsx`` and ``csv``.
    '''

    project_field = 'project'
    json_field = 'payload'
    schema_field = None
    schema_order = None
    attachment_field = None
    attachment_parent_field = None

    def get_queryset(self):
        '''
        Adds a dynamic filter to a viewset. Any query
        parameter prefixed by "{json_field}__" will filter entries
        based on the contents of <ViewSet>.<json_field>.

        Example:
        The URL "/submissions?payload__a__b__c=1" will yield
        the queryset

            models.Submission.objects.filter(payload__a__b__c=1)

        and return a list of submissions with a JSON payload like

            '{"a": {"b": {"c": 1}}}'

        Note that it is possible to compare not just strings, but
        numbers, lists and objects as well.
        '''

        def parse_value(value):
            try:
                return json.loads(value)
            except json.decoder.JSONDecodeError:
                return value

        json_filter = f'{self.json_field}__'
        filters = [
            # GET method: query params
            (k, v)
            for k, v in self.request.query_params.items()
            if k.startswith(json_filter)
        ] + [
            # POST method: data content
            (k, v)
            for k, v in self.request.data.items()
            if k.startswith(json_filter)
        ]
        queryset = self.queryset
        for k, v in filters:
            kwargs = {k: parse_value(v)}
            queryset = queryset.filter(**kwargs)
        return queryset

    @action(detail=False, methods=['get', 'post'])
    def query(self, request, *args, **kwargs):
        '''
        Allow to list data from a POST request.

        Reachable at ``.../{model}/query/``
        '''

        return self.list(request, *args, **kwargs)

    @action(detail=False, methods=['get', 'post'])
    def xlsx(self, request, *args, **kwargs):
        '''
        Export the data as an XLSX file

        Reachable at ``/{model}/xlsx/``
        '''
        return self.__export(request, file_format=XLSX_FORMAT)

    @action(detail=False, methods=['get', 'post'])
    def csv(self, request, *args, **kwargs):
        '''
        Export the data as a bunch of CSV files

        Reachable at ``/{model}/csv/``
        '''
        return self.__export(request, file_format=CSV_FORMAT)

    def __get(self, request, name, default=None):
        return request.query_params.get(name, dict(request.data).get(name, default))

    def __get_bool(self, request, name):
        return self.__get(request, name, '').lower() in ['true', 't']

    @transaction.non_atomic_requests
    def __export(self, request, file_format=CSV_FORMAT):
        '''
        Expected parameters:

        - Export options:

            - ``generate_attachments``, indicates if the file(s) with all
              the linked attachment files should be generated.

            - ``generate_records``, indicates if the file(s) with all the linked
              records should be generated. If the attachments are not included
              this option is true.

            - ``background``, indicates if instead of returning the file returns
              the task id linked to this export and continue the export process
              in background.
              Will be removed in release 2.0.

        - Data filtering:

            - ``page_size``, size of the block of data.
              Default: ``1048574``. The missing ones are reserved to the header.
              Total number of rows on a worksheet (since Excel 2007): ``1048576``.
              https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3

            - ``page``, current block of data.
              Default: ``1``.

            - ``start_at``, indicates the starting position. This allows to start at
              a custom position and not only at the beginning of the page block.
              Otherwise the ``page`` parameter is used to calculate it.

            - ``{json_field}__xxx``, json field filters.
              Handled by the ``get_queryset`` method.

            - ``exclude_files``, in case of generate attachments includes the
              regular expression of file names to exclude from the final zip file.
              Like: ``(audit\\.csv|\\.xml)$`` (this is the regex for ODK internal files)

              Read more in: https://www.postgresql.org/docs/9.6/functions-matching.html

        - File options:

            - ``filename``, name of the generated file (without extension).
              Default: first instance name (project/mappingset name) or ``export``.

            - ``paths``, using the AVRO schema definition for the data,
              the jsonpaths to be included.
              If missing will extract it from the schemas associated to the data
              along with the ``labels``.

              Example:
                  ["a.b", "a.c", ..., "z"]

            - ``labels``, the dictionary of labels for each jsonpath.
              If missing will use the jsonpaths or the one extracted from the schemas.

              Example:
                  {
                      "a": "A",
                      "a.b": "B",
                      "a.c": "C",
                      ...
                      "z": "Z"
                  }

            - ``header_content``, indicates what to include in the header.
              Options: ``labels`` (default), ``paths``, ``both`` (occupies two rows).

              Example:
                  With labels:    A / B   A / C   ... Z
                  With paths:     a/b     a/c     ... z
                  With both:      a/b     a/c     ... z
                                  A / B   A / C   ... Z

            - ``header_separator``, a one-character string used to separate the nested
              columns in the headers row.
              Default: slash ``/``.

              Example:
                  With labels:    A / B   A / C   ... Z
                  With paths:     a/b     a/c     ... z

            - ``header_shorten``, indicates if the header includes the full jsonpath/label
              or only the column one.
              Values: ``yes``, any other ``no``. Default: ``no``.

              Example:
                  With yes:       B       C       ... Z
                  Otherwise:      A / B   A / C   ... Z

            - ``data_format``, indicates how to parse the data into the file or files.
              Values: ``flatten``, any other ``split``. Default: ``split``.

              Example:

                  Data:

                      [
                          {
                              "id": "id1",
                              "payload": {
                                  "a": {
                                      "b": "1,2,3",
                                      "c": [0, 1, 2]
                                  },
                                  ...
                                  "z": 1
                              }
                          },
                          {
                              "id": "id2",
                              "payload": {
                                  "a": {
                                      "b": "a,b,c",
                                      "c": [4, 5]
                                  },
                                  ...
                                  "z": 2
                              }
                          }
                      ]

                  With flatten:

                      @   @ID   A / B   A / C / 1   A / C / 2   A / C / 3   ... Z
                      1   id1   1,2,3   0           1           2           ... 1
                      2   id2   a,b,c   4           5                       ... 2

                  Otherwise (with split):

                      Main file:
                          @   @ID   A / B   ... Z
                          1   id1   1,2,3   ... 1
                          2   id2   a,b,c   ... 2

                      A_C file:
                          @   @ID   A / C / #   A / C
                          1   id1   1           0
                          1   id1   2           1
                          1   id1   3           2
                          2   id2   1           4
                          2   id2   2           5

        - CSV format specific:

            - ``csv_escape``, a one-character string used to escape the separator
              and the quotechar char.
              Default: backslash ``\\``.

            - ``csv_quote``, a one-character string used to quote fields containing
              special characters, such as the separator or quote char, or which contain
              new-line characters.
              Default: double quotes ``"``.

            - ``csv_separator``, a one-character string used to separate the columns.
              Default: comma ``,``.

        '''
        queryset = self.filter_queryset(self.get_queryset())

        # Restriction: only export data for ONE PROJECT at a time
        if queryset.aggregate(p=Count(self.project_field, distinct=True))['p'] > 1:
            return Response(
                data={'message': _('Export data from one project at a time')},
                status=400,
            )

        # check pagination (positive values)
        page_size = max(1, int(self.__get(request, 'page_size', MAX_SIZE)))
        start_at = max(0, int(self.__get(request, 'start_at', '0')))
        if start_at > 0:
            offset = start_at - 1
        else:
            current_page = int(self.__get(request, 'page', '1'))
            offset = (current_page - 1) * page_size

        limit = min(queryset.count(), offset + page_size)
        if offset >= limit:
            return Response(status=204)  # NO-CONTENT

        project = getattr(queryset.first(), self.project_field)
        filename = self.__get(request, 'filename', queryset.first().name or 'export')
        export_settings = {
            'offset': offset,
            'limit': limit,
            'records': {},
            'attachments': {},
        }

        generate_attachments = self.__get_bool(request, 'generate_attachments')
        generate_attachments = (
            generate_attachments and
            self.attachment_field and
            self.attachment_parent_field
        )
        if generate_attachments:
            exclude_files = self.__get(request, 'exclude_files')

            queryset_attachs = queryset.exclude(**{self.attachment_field: None})
            if queryset_attachs.count() > 0:
                with connection.cursor() as cursor:
                    sql, params = queryset.values(EXPORT_FIELD_ID).query.sql_with_params()
                    query = cursor.mogrify(sql, params).decode('utf-8')

                export_settings['attachments'] = {
                    'query': query,
                    'filename': f'{filename}-attachments',
                    'parent_field': self.attachment_parent_field,
                    'exclude_files': exclude_files,
                }

        generate_records = not generate_attachments or self.__get_bool(request, 'generate_records')
        if generate_records:
            data = queryset.annotate(**{EXPORT_FIELD_DATA: F(self.json_field)}) \
                           .values(EXPORT_FIELD_ID, EXPORT_FIELD_DATA)

            # extract jsonpaths and docs from linked schemas definition
            jsonpaths = self.__get(request, 'paths', [])
            docs = self.__get(request, 'labels', {})
            if self.schema_field and not jsonpaths:
                schemas = queryset.order_by(self.schema_order or self.schema_field) \
                                  .exclude(**{self.schema_field: None}) \
                                  .values(self.schema_field) \
                                  .distinct()
                for schema in schemas:
                    extract_jsonpaths_and_docs(
                        schema=schema.get(self.schema_field),
                        jsonpaths=jsonpaths,
                        docs=docs,
                    )

            # check valid values for each option
            header_content = self.__get(request, 'header_content', settings.EXPORT_HEADER_CONTENT).lower()
            if header_content not in ('labels', 'paths', 'both'):
                header_content = 'labels'

            header_separator = self.__get(request, 'header_separator', settings.EXPORT_HEADER_SEPARATOR)
            if not header_separator:
                header_separator = settings.EXPORT_HEADER_SEPARATOR

            header_shorten = self.__get(request, 'header_shorten', settings.EXPORT_HEADER_SHORTEN).lower()
            if header_shorten != 'yes':
                header_shorten = 'no'

            data_format = self.__get(request, 'data_format', settings.EXPORT_DATA_FORMAT).lower()
            if data_format != 'flatten':
                data_format = 'split'

            csv_sep = self.__get(request, 'csv_separator', settings.EXPORT_CSV_SEPARATOR)
            if csv_sep == 'TAB':
                csv_sep = '\t'

            with connection.cursor() as cursor:
                sql, params = data.query.sql_with_params()
                query = cursor.mogrify(sql, params).decode('utf-8')

            export_settings['records'] = {
                'query': query,
                'file_format': file_format,
                'filename': filename,
                'paths': jsonpaths,
                'labels': docs,
                'export_options': {
                    'header_content': header_content,
                    'header_separator': header_separator,
                    'header_shorten': header_shorten,
                    'data_format': data_format,
                },
                'dialect_options': {
                    'delimiter': csv_sep,
                    'escapechar': self.__get(request, 'csv_escape', settings.EXPORT_CSV_ESCAPE),
                    'quotechar': self.__get(request, 'csv_quote', settings.EXPORT_CSV_QUOTE),
                },
            }

        if generate_attachments and not export_settings['attachments'] and not generate_records:
            # there are no attachments to download
            return Response(status=204)  # NO-CONTENT

        # create task with all need data
        task_id = ExportTask.objects.create(
            name=filename,
            created_by=request.user,
            project=project,
            settings=export_settings,
            status_records='INIT' if export_settings['records'] else None,
            status_attachments='INIT' if export_settings['attachments'] else None,
        ).pk

        # The subprocesses are executed outside the main thread,
        # we need to close the current connection and
        # each subprocess will open a new one.
        # Avoids:
        #   psycopg2.InterfaceError: connection already closed
        #   django.db.utils.OperationalError: server closed the connection unexpectedly
        connection.close()

        # start download subprocess(-es) and return task id
        processes = []
        if generate_records:
            processes.append(
                Process(
                    target=execute_records_task,
                    args=(task_id,),
                    name=f'task-records:{task_id}',
                )
            )

        if export_settings['attachments']:
            processes.append(
                Process(
                    target=execute_attachments_task,
                    args=(task_id,),
                    name=f'task-attachments:{task_id}',
                )
            )

        for p in processes:
            p.start()

        # ----------------------------------------------------------------------
        # Backward compatibility
        # In release 2.0 all the export requests will be executed in background
        # ----------------------------------------------------------------------

        # always execute export in background if it generates the attachment files
        if export_settings['attachments'] or self.__get_bool(request, 'background'):
            if settings.TESTING:  # pragma: no cover
                # In tests wait for the processes to finish
                for p in processes:
                    p.join()
                    p.close()

            return Response(data={'task': str(task_id)})

        # from this point only records download expected
        err_msg = _('Got an error while creating the file')

        for p in processes:
            p.join()   # join to main thread
            p.close()  # release resources

        if ExportTask.objects.filter(pk=task_id).exists():
            task = ExportTask.objects.get(pk=task_id)
            if task.status_records == 'DONE':
                return task.files.first().get_content(as_attachment=True)
            if task.error_records:
                return Response(data={'detail': err_msg + ': ' + task.error_records}, status=500)

        return Response(data={'detail': err_msg}, status=500)  # pragma: no cover


def execute_records_task(task_id):
    def __exec(counter):
        try:
            __generate_csv_files(
                temp_dir,
                _settings['query'],
                _settings['paths'],
                _settings['labels'],
                _offset,
                _limit,
                _settings['export_options'],
                dialect_name,
                counter,
            )
        except Exception as e:
            logger.warning(f'Got an error while generating records file: {str(e)}')
            task.set_error_records(str(e))
            raise  # required to force exitcode != 0

    if not ExportTask.objects.filter(pk=task_id).exists():
        return

    dialect_name = f'aether_custom_{str(task_id)}'
    task = ExportTask.objects.get(pk=task_id)

    try:
        _settings = task.settings['records']

        # register CSV dialect for the given options
        csv.register_dialect(
            dialect_name,
            delimiter=_settings['dialect_options']['delimiter'],
            doublequote=False,
            escapechar=_settings['dialect_options']['escapechar'],
            quotechar=_settings['dialect_options']['quotechar'],
            quoting=csv.QUOTE_NONNUMERIC,
        )

        _file_format = _settings['file_format']
        _offset = task.settings['offset']
        _limit = task.settings['limit']
        total = _limit - _offset

        task.set_status_records('WIP')

        logger.info(f'Preparing {_file_format} file: offset {_offset}, limit {_limit}')
        logger.info(str(_settings['export_options']))

        # temporary directory to keep the generated files
        with tempfile.TemporaryDirectory() as temp_dir:
            connection.close()

            counter = Value('i', 0)
            # execute in another thread to check if the task was deleted
            # (allow us to kill it instead of waiting for its conclusion)
            p = Process(target=__exec, args=(counter,), name=f'task-records:{task_id}:0')
            p.start()

            while p.is_alive():
                if not ExportTask.objects.filter(pk=task_id).exists():  # pragma: no cover
                    # the task was removed, stop the execution
                    p.kill()
                else:
                    value = counter.value / total
                    task.set_status_records(f'{value:.0%}')

                time.sleep(.1)  # wait

            failure = (p.exitcode != 0)
            p.close()

            if failure or not ExportTask.objects.filter(pk=task_id).exists():
                return

            _csv_files = {
                f.split('.')[0]: os.path.join(temp_dir, f)
                for f in os.listdir(temp_dir)
                if os.path.isfile(os.path.join(temp_dir, f)) and not f.startswith('temp-')
            }
            # order object keys and reformat leading zeros depending on total number
            _sorted_keys = sorted(_csv_files.keys(), key=lambda x: int(x))
            csv_files = {
                k: _csv_files[k]
                for k in _sorted_keys
            }

            filename = _settings['filename']
            task.set_status_records(f'{_file_format}…')
            if _file_format == XLSX_FORMAT:
                file_name, file_path = __prepare_xlsx(temp_dir, csv_files, filename, dialect_name)
            else:
                file_name, file_path = __prepare_zip(temp_dir, csv_files, filename)

            task.set_status_records(_file_format)
            with open(file_path, 'rb') as f:
                export_file = ExportTaskFile(task=task)
                export_file.file.save(file_name, File(f))
                export_file.size = os.path.getsize(file_path)
                export_file.save()

        task.set_status_records('DONE')
        logger.info(f'File "{file_name}" ready!')

    except Exception as e:
        logger.debug(f'Got an error while generating records file: {str(e)}')
        task.set_error_records(str(e))
        raise  # required to force exitcode != 0

    finally:
        csv.unregister_dialect(dialect_name)


def execute_attachments_task(task_id):
    def _fetch_attachs(_start, _stop, counter, counter_attachs):
        try:
            logger.debug(f'Downloading attachments from {_start} to {_stop}')

            with connection.cursor() as cursor:
                data_from = _start
                while data_from < _stop:
                    data_to = min(data_from + ATTACHMENTS_PAGE_SIZE, _stop)
                    logger.debug(f'Downloading attachments {data_from} to {data_to}')

                    # get parent ids
                    cursor.execute(f'{sql} OFFSET {data_from} LIMIT {data_to - data_from}')
                    _parent_ids = set([_row[0] for _row in cursor.fetchall()])

                    # get attachments
                    for _parent_id in _parent_ids:
                        _attachments = Attachment.objects.filter(**{parent_field: _parent_id})
                        if exclude_files:
                            _attachments = _attachments.exclude(name__iregex=exclude_files)

                        if _attachments.count():
                            _directory = f'{temp_dir}/files/{_parent_id}'
                            os.makedirs(_directory, exist_ok=True)

                            # Get the attachments list,
                            # download their content from the storage
                            for _attachment in _attachments.distinct():
                                _aname = _attachment.name.split('/')[-1]
                                with open(f'{_directory}/{_aname}', 'wb') as _file:
                                    _file.write(_attachment.get_content().getvalue())
                                with counter_attachs.get_lock():
                                    counter_attachs.value += 1

                        with counter.get_lock():
                            counter.value += 1

                    # next iteration
                    data_from = data_to

        except Exception as e:
            logger.debug(f'Got an error while generating attachments file: {str(e)}')
            task.set_error_attachments(str(e))
            raise  # required to force exitcode != 0

    if not ExportTask.objects.filter(pk=task_id).exists():
        return

    task = ExportTask.objects.get(pk=task_id)

    try:

        # temporary directory to keep the generated files
        with tempfile.TemporaryDirectory() as temp_dir:
            _settings = task.settings['attachments']

            # These values belong to the parent model
            # We iterate the parent model instead of the attachments
            # to match the "records" file content with this.
            offset = task.settings['offset']
            limit = task.settings['limit']
            total = limit - offset

            filename = _settings['filename']
            sql = _settings['query']
            parent_field = _settings['parent_field']
            exclude_files = _settings['exclude_files']

            task.set_status_attachments('WIP')
            logger.info(f'Preparing attachments file: offset {offset}, limit {limit}')

            chunk_size = max(1, int(total / settings.EXPORT_NUM_CHUNKS))

            connection.close()
            processes = []
            counter = Value('i', 0)
            counter_attachs = Value('i', 0)

            data_from = offset
            while data_from < limit:
                data_to = min(data_from + chunk_size, limit)
                # download in parallel
                processes.append(
                    Process(
                        target=_fetch_attachs,
                        args=(data_from, data_to, counter, counter_attachs,),
                        name=f'task-attachments:{task_id}:{data_from}:{data_to}',
                    )
                )
                data_from = data_to  # next

            for p in processes:  # start
                p.start()

            while any(map(lambda x: x.is_alive(), processes)):
                if (
                    # one of the processes failed
                    any(map(lambda x: (not x.is_alive() and x.exitcode != 0), processes))
                    or
                    # the task was deleted
                    not ExportTask.objects.filter(pk=task_id).exists()
                ):  # pragma: no cover
                    # terminate all processes, one failed
                    for p in processes:
                        p.kill()
                else:
                    value = counter.value / total
                    task.set_status_attachments(f'{value:.0%}')
                time.sleep(.1)  # wait

            failure = any(map(lambda x: x.exitcode != 0, processes))
            for p in processes:  # release resources
                p.close()

            if failure or not ExportTask.objects.filter(pk=task_id).exists():
                return

            if counter_attachs.value == 0:
                task.set_error_attachments(_('No attachments found!'))
                return

            logger.debug('All attachments downloaded!')

            # create zip with attachments and add to task files
            task.set_status_attachments('ZIP…')
            zip_ext = 'zip'
            zip_name = f'{filename}-{datetime.now().isoformat()}'
            zip_path = shutil.make_archive(
                base_name=f'{temp_dir}/{zip_name}',
                format=zip_ext,
                root_dir=f'{temp_dir}/files/',
            )

            # TODO: split in several files depending on final size
            file_size = os.path.getsize(zip_path)
            zip_size = sizeof_fmt(file_size)
            logger.debug(
                f'Generated attachments file "{zip_path}" with size: {zip_size}.'
            )
            task.set_status_attachments(f'ZIP ({zip_size})')
            if file_size > MAX_FILE_SIZE:  # pragma: no cover
                logger.warning(
                    f'The file size ({zip_size}) might cause problems'
                    ' in FAT32 disks or with old ZIP versions'
                )

            with open(zip_path, 'rb') as f:
                export_file = ExportTaskFile(task=task)
                export_file.file.save(f'{zip_name}.{zip_ext}', File(f))
                export_file.size = file_size
                export_file.save()

            task.set_status_attachments('DONE')
            logger.info(f'File "{zip_name}.{zip_ext}" ready!')

    except Exception as e:
        logger.debug(f'Got an error while generating attachments file: {str(e)}')
        task.set_error_attachments(str(e))


def __prepare_zip(temp_dir, csv_files, filename):
    zip_name = f'{filename}-{datetime.now().isoformat()}.zip'
    zip_path = f'{temp_dir}/{zip_name}'
    num_files = len(csv_files.keys()) - 1
    num_zeros = math.floor(math.log10(num_files) if num_files > 9 else 0)

    with zipfile.ZipFile(zip_path, 'w') as csv_zip:
        for key, value in csv_files.items():
            csv_name = f'{filename}.csv' if key == '0' else f'{filename}.{key.zfill(num_zeros)}.csv'
            csv_zip.write(value, csv_name)

    return zip_name, zip_path


def __prepare_xlsx(temp_dir, csv_files, filename, dialect=DEFAULT_DIALECT):
    wb = Workbook(write_only=True, iso_dates=True)
    for key, value in csv_files.items():
        ws = wb.create_sheet(key)
        with open(value, newline='') as f:
            reader = csv.reader(f, dialect=dialect)
            for line in reader:
                ws.append(line)

    xlsx_name = f'{filename}-{datetime.now().isoformat()}.xlsx'
    xlsx_path = f'{temp_dir}/{xlsx_name}'
    wb.save(xlsx_path)
    wb.close()

    return xlsx_name, xlsx_path


#
# Parses data and includes them in the csv files.
#
# Steps per data row:
#   1. Flatten the row into a one level object with its path as key.
#   2. Identifies row attributes, key name starts with "@".
#   3. If one of the row keys contains an array, instead of flatten it
#      creates a new csv group and includes there the array entries
#      (including the row attributes in each one) as rows.
#
# @param {str}   sql     - SQL sentence
# @param {list}  paths   - the list of allowed paths
# @param {dict}  labels  - a dictionary with header labels
#
def __generate_csv_files(
        temp_dir,
        sql,
        paths,
        labels,
        offset=0,
        limit=MAX_SIZE,
        export_options=DEFAULT_OPTIONS,
        dialect=DEFAULT_DIALECT,
        counter=None,
):
    def add_header(options, header):
        if header not in options['headers_set']:
            options['headers_set'].add(header)
            options['headers'].append(header)

    def append_entry(options, entry):
        options['csv_file'].writerow([
            entry.get(header, '')
            for header in options['headers']
        ])

    def get_current_options(group, header_ids):
        try:
            return csv_options[group]
        except KeyError:
            # new
            title = '0' if group == '$' else str(len(csv_options.keys()))
            csv_path = os.path.join(temp_dir, f'temp-{title}.csv')
            f = open(csv_path, 'w', newline='')
            c = csv.writer(f, dialect=dialect)

            csv_options[group] = {
                'file': f,
                'csv_path': csv_path,
                'csv_file': c,
                'title': title,

                'headers_set': set(),  # faster search but breaks insertion order
                'headers': list(header_ids),
            }

            return csv_options.get(group)

    def get_full_key(key, group):
        return key if group == '$' else f'{group}.{key}'

    def walker(item, item_ids, group):
        current = get_current_options(group, item_ids.keys())

        entry = {**item_ids}
        for key in item.keys():
            value = item[key]
            full_key = get_full_key(key, group)

            if not isinstance(value, list):
                add_header(current, full_key)
                entry[full_key] = value

            else:
                # create array group and walk array elements in it
                array_group = f'{full_key}.{ARRAY_PATH}'
                i = 0
                for val in value:
                    i += 1
                    element = __flatten_dict(val) if isinstance(val, dict) else {'': val}
                    element_ids = {
                        **item_ids,             # identifies the parent
                        f'@.{array_group}': i,  # identifies the element
                    }
                    walker(element, element_ids, array_group)

        append_entry(current, entry)

    # start generation
    flatten_list = (export_options['data_format'] == 'flatten')
    csv_options = {}
    paths = __filter_paths(paths)

    # paginate results to reduce memory usage
    with connection.cursor() as cursor:
        data_from = offset
        while data_from < limit:
            data_to = min(data_from + RECORDS_PAGE_SIZE, limit)
            logger.debug(f'From {data_from} to {data_to}')

            cursor.execute(f'{sql} OFFSET {data_from} LIMIT {data_to - data_from}')
            columns = [col[0] for col in cursor.description]
            for entry in cursor:
                row = dict(zip(columns, entry))
                data_from += 1
                json_data = __flatten_dict(row.get(EXPORT_FIELD_DATA), flatten_list)
                walker(json_data, {'@': data_from, '@id': str(row.get(EXPORT_FIELD_ID))}, '$')
                if counter:  # pragma: no cover
                    with counter.get_lock():
                        counter.value += 1

    logger.debug('Building headers')

    # include headers and row columns in order
    csv_files = {}
    for group in csv_options.keys():
        current = csv_options[group]
        current['file'].close()

        title = current['title']
        csv_path = os.path.join(temp_dir, f'{title}.csv')
        rows_path = current['csv_path']

        # create headers in order
        headers = __filter_headers(paths, group, current['headers'])
        if headers:
            with open(rows_path, newline='') as fr, open(csv_path, 'w', newline='') as fw:
                r = csv.DictReader(fr, fieldnames=current['headers'], dialect=dialect)
                w = csv.writer(fw, dialect=dialect)

                single = (export_options['header_shorten'] == 'yes')
                joiner = export_options['header_separator']

                # paths header
                if export_options['header_content'] in ('paths', 'both'):
                    w.writerow([
                        __get_label(header,
                                    labels,
                                    content='path',
                                    single=single,
                                    joiner=joiner,
                                    )
                        for header in headers
                    ])

                # labels header
                if export_options['header_content'] in ('labels', 'both'):
                    w.writerow([
                        __get_label(header,
                                    labels,
                                    content='label',
                                    single=single,
                                    joiner=f' {joiner} ',
                                    )
                        for header in headers
                    ])

                for row in r:
                    w.writerow([
                        row.get(header, '')
                        for header in headers
                    ])
            csv_files[title] = csv_path

    return csv_files


def __flatten_dict(obj, flatten_list=False):
    def _items():
        for key, value in obj.items():
            if isinstance(value, list) and flatten_list:
                value = {str(i): v for i, v in enumerate(value, start=1)}

            if isinstance(value, dict):
                for subkey, subvalue in __flatten_dict(value, flatten_list).items():
                    yield f'{key}.{subkey}', subvalue
            else:
                yield key, value
    return dict(_items())


def __filter_paths(paths):
    filtered_paths = [
        path
        for path in paths
        if (
            # remove attributes
            not path.startswith('@') and
            # remove aether internal fields
            f'{ENTITY_EXTRACTION_ENRICHMENT}.' not in path and
            f'{ENTITY_EXTRACTION_ERRORS}.' not in path and
            path not in [ENTITY_EXTRACTION_ENRICHMENT, ENTITY_EXTRACTION_ERRORS] and
            # remove array/ map/ union paths
            f'.{ARRAY_PATH}' not in path and
            f'.{MAP_PATH}' not in path and
            f'.{UNION_PATH}' not in path
        )
    ]
    # keep only leafs!!!
    leafs = [
        path
        for path in filtered_paths
        if len([p for p in filtered_paths if p.startswith(f'{path}.')]) == 0
    ]
    return leafs


def __filter_headers(paths, group, headers):
    # create headers in order
    filtered_headers = None
    if not paths:
        filtered_headers = headers  # appearance order
    else:
        if group == '$':
            filtered_headers = ['@', '@id']
            for path in paths:
                for header in headers:
                    if header == path or header.startswith(f'{path}.'):
                        filtered_headers.append(header)
        else:
            # check that the group is in the paths list
            for path in paths:
                if group == path or group.startswith(f'{path}.'):
                    return headers

    if group != '$':  # only the main group can have flattened list
        return filtered_headers
    return __order_headers(filtered_headers)


def __order_headers(headers):
    '''
    ISSUE: order the headers so the nested arrays appear together and in order.
    The sorting algorithm MUST be STABLE (luckly python "sorted" method is).

    ASSUMPTIONS:
        a) The are no numeric properties outside the nested list items. (AVRO naming restrictions)
        b) The numerical properties appear in order in the list starting with 1. [1, 2, 3, ...]
        c) There are no gaps between two consecutive numerical properties.  [..., n, ..., n+1, ...]

    These cases are not possible:
        ``2`` before ``1``:
            [ ..., "any_path.2.and_more", ..., "any_path.1.and_more",... ]
        ``1`` and ``3`` without ``2``:
            [ ..., "any_path.1.and_more", ..., "any_path.3.and_more",... ]

    IMPLEMENTED SOLUTION: assign a weigth to each list element

        A) it's not a flatten array element
                then set its position in the array

        B) it's a flatten array element
              then set the same weigth as the first flatten element in the list
              along with its index (recursively)
              For "any_path.3.and_more" set ("any_path" row, 3) pair

        Index   Element     Weight 1      Weight 2    Weight 3      Weight 4    Weight 5
                            (# row 1st)   (index)     (# row 1st)   (index)     (# row 1st)
        1.-     ZZZ         -> 1
        2.-     w.2.b.1     -> 2          -> 2        -> 2          -> 1        -> 2  << !!never happens (disorder)
        3.-     w.1.a.1     -> 2          -> 1        -> 3          -> 1        -> 3
        4.-     w.2.a       -> 2          -> 2        -> 4
        5.-     XXX         -> 5
        6.-     b.2         -> 6          -> 2        -> 6                            << !!never happens (no 1st)
        7.-     w.3         -> 2          -> 3        -> 7
        8.-     w.2.b.2     -> 2          -> 2        -> 2          -> 2        -> 8
        9.-     YYY         -> 9
        10.-    c.1         -> 10         -> 1        -> 10
        11.-    w.1.c.1     -> 2          -> 1        -> 11         -> 1        -> 11
        12.-    w.1.c.2     -> 2          -> 1        -> 11         -> 2        -> 12
        13.-    c.2         -> 10         -> 2        -> 13
        14.-    b.4         -> 6          -> 4        -> 14                           << !!never happens (gap)

    Sorted by weights:

        Index   Element     Weight 1      Weight 2    Weight 3      Weight 4    Weight 5
                            (# row 1st)   (index)     (# row 1st)   (index)     (# row 1st)
        1.-     ZZZ         -> 1
        3.-     w.1.a.1     -> 2          -> 1        -> 3          -> 1        -> 3
        11.-    w.1.c.1     -> 2          -> 1        -> 11         -> 1        -> 11
        12.-    w.1.c.2     -> 2          -> 1        -> 11         -> 2        -> 12
        2.-     w.2.b.1     -> 2          -> 2        -> 2          -> 1        -> 2
        8.-     w.2.b.2     -> 2          -> 2        -> 2          -> 2        -> 8
        4.-     w.2.a       -> 2          -> 2        -> 4
        7.-     w.3         -> 2          -> 3        -> 7
        5.-     XXX         -> 5
        6.-     b.2         -> 6          -> 2        -> 6
        14.-    b.4         -> 6          -> 4        -> 14
        9.-     YYY         -> 9
        10.-    c.1         -> 10         -> 1        -> 10
        13.-    c.2         -> 10         -> 2        -> 13

    '''

    # check that there are flattened lists
    weighted_headers = []
    position_by_path = {}
    max_weight_size = 1
    for index, header in enumerate(headers):
        weighted_headers.append([header, [index]])

        if __is_flatten(header):
            # divide the header into pieces and set the current position for each numerical entry
            # a.4.b.5.c.6.z  ==>  (a.4, a.4.b.5, a.4.b.5.c.6)
            pieces = header.split('.')
            for i in range(len(pieces)):
                if __is_int(pieces[i]):
                    first = '.'.join(pieces[:i])
                    position_by_path[first] = min(position_by_path.get(first, index), index)

            # calculate weight size
            size = 1 + 2 * (
                len(RE_CONTAINS_DIGIT.findall(header)) +
                len(RE_ENDSWITH_DIGIT.findall(header))
            )
            max_weight_size = max(max_weight_size, size)

    if max_weight_size == 1:
        return headers

    for index, header in enumerate(headers):
        if __is_flatten(header):
            # a.4.b.5.c.6  ==>  (a row, 4, a.4.b row, 5, a.4.b.5.c row, 6, current row)
            weight = []
            pieces = header.split('.')
            for i in range(len(pieces)):
                if __is_int(pieces[i]):
                    first = '.'.join(pieces[:i])
                    weight += [position_by_path[first], int(pieces[i])]
            weight += [index]
            weighted_headers[index][1] = weight

    for i in range(max_weight_size - 1, -1, -1):
        weighted_headers.sort(key=lambda x: x[1][i] if len(x[1]) > i else 0)

    return [wh[0] for wh in weighted_headers]


def __get_label(jsonpath,
                labels={},
                content='label',
                single=False,
                joiner=' / ',
                ):
    def get_single(path):
        # find in the labels dictionary the jsonpath entry
        if labels.get(path):
            return labels.get(path)

        for key in labels.keys():
            # remove the UNION mark and try again
            clean_key = key.replace(f'{UNION_PATH}.', '').replace(f'.{UNION_PATH}', '')
            if path == clean_key:
                return labels.get(key)

            # check if it matches any MAP field
            # create the regular expression with the key value
            # "a.b.*.c.d.*.e" => /^a\.b\.([A-Za-z0-9_]+)\.c\.d\.([A-Za-z0-9_]+)\.e/$
            re_key = clean_key.replace(MAP_PATH, '([A-Za-z0-9_]+)').replace('.', '\\.')
            if re.compile(f'^{re_key}$').match(path):
                return labels.get(key)

        # otherwise return last key in path (prettified)
        # "a.b.c.some__thing__4_5_" => "Some thing 4 5"
        return path.split('.')[-1].replace('_', ' ').replace('  ', ' ').strip().capitalize()

    if jsonpath.startswith('@.'):
        jsonpath = jsonpath[2:]  # remove attribute identifier

    pieces = jsonpath.split('.')
    if content == 'path':
        return pieces[-1] if single else joiner.join(pieces)

    if single:
        # take only the last piece
        return get_single('.'.join(pieces))
    else:
        # the full label
        return joiner.join([get_single('.'.join(pieces[:i + 1])) for i in range(len(pieces))])


def __is_int(value):
    try:
        int(value, 10)
        return True
    except ValueError:
        return False


def __is_flatten(value):
    return RE_CONTAINS_DIGIT.search(value) or RE_ENDSWITH_DIGIT.search(value)


# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num):  # pragma: no cover
    '''
    Multiples of bytes (decimal):

        Value     Metric
        -------   --------------
        1000      KB  kilobyte
        1000^2    MB  megabyte
        1000^3    GB  gigabyte
        1000^4    TB  terabyte
        1000^5    PB  petabyte
        1000^6    EB  exabyte
        1000^7    ZB  zettabyte
        1000^8    YB  yottabyte
    '''
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
        if abs(num) < 1000.0:
            return '%3.1f%s' % (num, unit)
        num /= 1000.0
    return '%.1f%s' % (num, 'YB')
