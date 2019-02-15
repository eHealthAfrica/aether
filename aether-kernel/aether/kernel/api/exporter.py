# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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
from collections import namedtuple
import csv
import json
import logging
import os
import re
import tempfile
import uuid
import zipfile

from openpyxl import Workbook

from django.conf import settings
from django.db.models import F
from django.http import FileResponse
from django.utils.translation import ugettext as _

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action

from .avro_tools import ARRAY_PATH, MAP_PATH, UNION_PATH, extract_jsonpaths_and_docs
from .entity_extractor import ENTITY_EXTRACTION_ENRICHMENT, ENTITY_EXTRACTION_ERRORS


RE_CONTAINS_DIGIT = re.compile(r'\.\d+\.')  # a.999.b
RE_ENDSWITH_DIGIT = re.compile(r'\.\d+$')   # a.b.999

EXPORT_DIR = tempfile.mkdtemp()

CSV_FORMAT = 'csv'
CSV_CONTENT_TYPE = 'application/zip'

XLSX_FORMAT = 'xlsx'
XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# Total number of rows on a worksheet (since Excel 2007): 1048576
# https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3
MAX_SIZE = 1048574  # the missing ones are the header ones (paths & labels)
PAGE_SIZE = 1000

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

ExportOptions = namedtuple(
    'ExportOptions', [
        'header_content',
        'header_separator',
        'header_shorten',
        'data_format',
        'csv_dialect',
    ])

DEFAULT_OPTIONS = ExportOptions(
    header_content=settings.EXPORT_HEADER_CONTENT,
    header_separator=settings.EXPORT_HEADER_SEPARATOR,
    header_shorten=settings.EXPORT_HEADER_SHORTEN,
    data_format=settings.EXPORT_DATA_FORMAT,
    csv_dialect=DEFAULT_DIALECT,
)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExporterViewSet(ModelViewSet):
    '''
    ModelViewSet that includes export endpoints ``xlsx`` and ``csv``.
    '''

    json_field = 'payload'
    schema_field = None
    schema_order = None

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
        return self.__export(request, format=XLSX_FORMAT)

    @action(detail=False, methods=['get', 'post'])
    def csv(self, request, *args, **kwargs):
        '''
        Export the data as a bunch of CSV files

        Reachable at ``/{model}/csv/``
        '''
        return self.__export(request, format=CSV_FORMAT)

    def __get(self, request, name, default=None):
        return request.query_params.get(name, dict(request.data).get(name, default))

    def __options(self, request):
        # register CSV dialect for the given options
        dialect_name = f'aether_custom_{str(uuid.uuid4())}'
        csv_sep = self.__get(request, 'csv_separator', settings.EXPORT_CSV_SEPARATOR)
        if csv_sep == 'TAB':
            csv_sep = '\t'

        csv.register_dialect(
            dialect_name,
            delimiter=csv_sep,
            doublequote=False,
            escapechar=self.__get(request, 'csv_escape', settings.EXPORT_CSV_ESCAPE),
            quotechar=self.__get(request, 'csv_quote', settings.EXPORT_CSV_QUOTE),
            quoting=csv.QUOTE_NONNUMERIC,
        )

        # check valid values for each option
        header_content = self.__get(request, 'header_content', settings.EXPORT_HEADER_CONTENT)
        if header_content not in ('labels', 'paths', 'both'):
            header_content = 'labels'

        header_separator = self.__get(request, 'header_separator', settings.EXPORT_HEADER_SEPARATOR)
        if not header_separator:
            header_separator = settings.EXPORT_HEADER_SEPARATOR

        header_shorten = self.__get(request, 'header_shorten', settings.EXPORT_HEADER_SHORTEN)
        if header_shorten != 'yes':
            header_shorten = 'no'

        data_format = self.__get(request, 'data_format', settings.EXPORT_DATA_FORMAT)
        if data_format != 'flatten':
            data_format = 'split'

        return ExportOptions(
            header_content=header_content,
            header_separator=header_separator,
            header_shorten=header_shorten,
            data_format=data_format,
            csv_dialect=dialect_name,
        )

    def __export(self, request, format=CSV_FORMAT):
        '''
        Expected parameters:

        Data filtering:

        - ``page_size``, size of the block of data.
            Default: ``1048574``. The missing ones are reserved to the header.
            Total number of rows on a worksheet (since Excel 2007): ``1048576``.
            https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3

        - ``page``, current block of data.
            Default: ``1``.

        - ``start_at``: indicates the starting position. This allows to start at
            a custom position and not only at the beginning of the page block.
            Otherwise the ``page`` parameter is used to calculate it.

        - ``{json_field}__xxx``, json field filters. Handled by the ``get_queryset`` method.

        File options:

        - ``filename``, name of the generated file (without extension).
            Default: first instance name (project/mappingset name) or ``export``.

        - ``paths``, using the AVRO schema definition for the data, the jsonpaths to be included.
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

        - ``data_format``: indicates how to parse the data into the file or files.
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

        CSV format specific:

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
        data = queryset.annotate(exporter_data=F(self.json_field)) \
                       .values('pk', 'exporter_data')

        # check pagination (positive values)
        page_size = max(1, int(self.__get(request, 'page_size', MAX_SIZE)))
        start_at = max(0, int(self.__get(request, 'start_at', '0')))
        if start_at > 0:
            offset = start_at - 1
        else:
            current_page = int(self.__get(request, 'page', '1'))
            offset = (current_page - 1) * page_size

        limit = min(data.count(), offset + page_size)
        if offset >= limit:
            return Response(status=204)  # NO-CONTENT

        # extract jsonpaths and docs from linked schemas definition
        jsonpaths = self.__get(request, 'paths', [])
        docs = self.__get(request, 'labels', {})
        if self.schema_field and not jsonpaths:
            schemas = queryset.order_by(self.schema_order or self.schema_field) \
                              .values(self.schema_field) \
                              .distinct()
            for schema in schemas:
                extract_jsonpaths_and_docs(
                    schema=schema.get(self.schema_field),
                    jsonpaths=jsonpaths,
                    docs=docs,
                )

        options = self.__options(request)

        try:
            logger.info(f'Preparing {format} file: offset {offset}, limit {limit}')
            logger.info(str(options))
            file_name, file_path, content_type = generate_file(
                data=data,
                format=format,
                # use the first instance to build the filename
                filename=self.__get(request, 'filename', queryset.first().name or 'export'),
                paths=jsonpaths,
                labels=docs,
                offset=offset,
                limit=limit,
                options=options,
            )
            csv.unregister_dialect(options.csv_dialect)
            logger.info(f'File "{file_name}" ready!')

            response = FileResponse(open(file_path, 'rb'))
            response['Content-Type'] = content_type
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            response['Content-Length'] = os.path.getsize(file_path)
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'

            return response

        except IOError as e:
            csv.unregister_dialect(options.csv_dialect)
            msg = _('Got an error while creating the file: {error}').format(error=str(e))
            return Response(data={'detail': msg}, status=500)


def generate_file(data,
                  paths=[],
                  labels={},
                  format=CSV_FORMAT,
                  filename='export',
                  offset=0,
                  limit=MAX_SIZE,
                  options=DEFAULT_OPTIONS,
                  ):
    '''
    Generates an XLSX/ ZIP (of CSV files) file with the given data.

    - ``data`` is a queryset with two main properties ``pk`` and ``exporter_data``.
    - ``format``, expected values ``xlsx`` or ``csv``.
    - ``paths`` is a list with the allowed jsonpaths.
    - ``labels`` is a dictionary whose keys are the jsonpaths
      and the values the linked labels to use as header for that jsonpath.
    - ``options`` the export options.
    '''

    csv_files = __generate_csv_files(data, paths, labels, offset, limit, options)
    if format == XLSX_FORMAT:
        return __prepare_xlsx(csv_files, filename, options.csv_dialect)
    else:
        return __prepare_zip(csv_files, filename)


def __prepare_zip(csv_files, filename):
    zip_name = f'{filename}-{datetime.now().isoformat()}.zip'
    zip_path = EXPORT_DIR + '/' + filename
    with zipfile.ZipFile(zip_path, 'w') as csv_zip:
        for key, value in csv_files.items():
            csv_name = f'{filename}.csv' if key == '0' else f'{filename}.{key}.csv'
            csv_zip.write(value, csv_name)

    return zip_name, zip_path, CSV_CONTENT_TYPE


def __prepare_xlsx(csv_files, filename, csv_dialect):
    wb = Workbook(write_only=True, iso_dates=True)
    for key, value in csv_files.items():
        ws = wb.create_sheet(key)
        with open(value, newline='') as f:
            reader = csv.reader(f, dialect=csv_dialect)
            for line in reader:
                ws.append(line)

    xlsx_name = f'{filename}-{datetime.now().isoformat()}.xlsx'
    xlsx_path = EXPORT_DIR + '/' + xlsx_name
    wb.save(xlsx_path)
    wb.close()

    return xlsx_name, xlsx_path, XLSX_CONTENT_TYPE


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
# @param {list}  data    - raw data
# @param {list}  paths   - the list of allowed paths
# @param {dict}  labels  - a dictionary with header labels
#
def __generate_csv_files(data, paths, labels, offset=0, limit=MAX_SIZE, export_options=DEFAULT_OPTIONS):
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
            csv_path = f'{EXPORT_DIR}/temp-{title}.csv'
            f = open(csv_path, 'w', newline='')
            c = csv.writer(f, dialect=export_options.csv_dialect)

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
    flatten_list = (export_options.data_format == 'flatten')
    csv_options = {}
    paths = __filter_paths(paths)

    # paginate results to reduce memory usage
    data_from = offset
    index = offset
    while data_from < limit:
        data_to = min(data_from + PAGE_SIZE, limit)
        logger.debug(f'From {data_from} to {data_to}')

        for row in data[data_from:data_to]:
            index += 1
            json_data = __flatten_dict(row.get('exporter_data'), flatten_list)
            walker(json_data, {'@': index, '@id': str(row.get('pk'))}, '$')
        data_from = data_to

    logger.debug('Building headers')

    # include headers and row columns in order
    csv_files = {}
    for group in csv_options.keys():
        current = csv_options[group]
        current['file'].close()

        title = current['title']
        csv_path = f'{EXPORT_DIR}/{title}.csv'
        rows_path = current['csv_path']

        # create headers in order
        headers = __filter_headers(paths, group, current['headers'])
        if headers:
            with open(rows_path, newline='') as fr, open(csv_path, 'w', newline='') as fw:
                r = csv.DictReader(fr, fieldnames=current['headers'], dialect=export_options.csv_dialect)
                w = csv.writer(fw, dialect=export_options.csv_dialect)

                single = (export_options.header_shorten == 'yes')

                # paths header
                if export_options.header_content in ('paths', 'both'):
                    w.writerow([
                        __get_label(header,
                                    labels,
                                    content='path',
                                    single=single,
                                    joiner=export_options.header_separator,
                                    )
                        for header in headers
                    ])

                # labels header
                if export_options.header_content in ('labels', 'both'):
                    w.writerow([
                        __get_label(header,
                                    labels,
                                    content='label',
                                    single=single,
                                    joiner=f' {export_options.header_separator} ',
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
                    if header == path or header.startswith(path + '.'):
                        filtered_headers.append(header)
        else:
            # check that the group is in the paths list
            for path in paths:
                if group == path or group.startswith(path + '.'):
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
