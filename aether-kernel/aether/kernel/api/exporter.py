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
import csv
import os
import re
import tempfile
import zipfile

from openpyxl import Workbook

from django.db.models import F
from django.http import FileResponse
from django.utils.translation import ugettext as _

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action

from .avro_tools import ARRAY_PATH, MAP_PATH, UNION_PATH, extract_jsonpaths_and_docs
from ..settings import CSV_SEPARATOR

EXPORT_DIR = tempfile.mkdtemp()
FILENAME_RE = '{name}-{ts}.{ext}'

CSV_CONTENT_TYPE = 'application/zip'
XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# Total number of rows on a worksheet (since Excel 2007): 1048576
# https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3
MAX_SIZE = 1048575  # the missing one is the header
PAGE_SIZE = 1000


class ExporterViewSet(ModelViewSet):
    '''
    ModelViewSet that includes export endpoints ``xlsx`` and ``csv``.
    '''

    json_field = 'payload'
    schema_field = None
    schema_order = None

    @action(detail=False, methods=['get', 'post'])
    def xlsx(self, request, *args, **kwargs):
        '''
        Export the data as an XLSX file
        Reachable at ``/{model}/xlsx/``
        '''
        return self.__export(request, format='xlsx')

    @action(detail=False, methods=['get', 'post'])
    def csv(self, request, *args, **kwargs):
        '''
        Export the data as a bunch of CSV files
        Reachable at ``/{model}/csv/``
        '''
        return self.__export(request, format='csv')

    def __get(self, request, name, default=None):
        return request.GET.get(name, dict(request.data).get(name, default))

    def __export(self, request, format):
        queryset = self.filter_queryset(self.get_queryset())
        data = queryset.annotate(exporter_data=F(self.json_field)) \
                       .values('pk', 'exporter_data')

        # check pagination
        current_page = int(self.__get(request, 'page', '1'))
        page_size = int(self.__get(request, 'page_size', MAX_SIZE))

        offset = (current_page - 1) * page_size
        limit = min(data.count(), offset + page_size)
        if offset >= limit:
            return Response(status=204)  # NO-CONTENT

        # extract jsonpaths and docs from linked schemas definition
        jsonpaths = self.__get(request, 'paths', [])
        docs = self.__get(request, 'headers', {})
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

        try:
            filename, filepath, content_type = generate_file(
                data=data,
                paths=jsonpaths,
                labels=docs,
                format=format,
                filename=self.__get(request, 'filename', 'export'),
                offset=offset,
                limit=limit,
            )

            response = FileResponse(open(filepath, 'rb'))
            response['Content-Type'] = content_type
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = os.path.getsize(filepath)
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'

            return response

        except IOError as e:
            msg = _('Got an error while creating the file: {error}').format(error=str(e))
            return Response(data={'detail': msg}, status=500)


def generate_file(data, paths=[], labels={}, format='csv', filename='export', offset=0, limit=MAX_SIZE):
    '''
    Generates an XLSX/ ZIP (of CSV files) file with the given data.

    - ``data`` is a queryset with two main properties ``pk`` and ``exporter_data``.
    - ``paths`` is a list with the allowed jsonpaths.
    - ``labels`` is a dictionary which keys are the jsonpaths
      and the values the linked labels to use as header for that jsonpath.
    - ``format``, expected values ``xlsx`` or ``csv``.
    '''

    csv_options = __generate_csv_files(data, paths, labels, offset, limit)
    if format == 'xlsx':
        return __prepare_xlsx(csv_options, filename)
    else:
        return __prepare_zip(csv_options, filename)


def __prepare_zip(csv_options, filename):
    zip_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='zip')
    zip_path = EXPORT_DIR + '/' + filename
    with zipfile.ZipFile(zip_path, 'w') as csv_zip:
        for options in csv_options.values():
            csv_name = FILENAME_RE.format(name=filename, ts=options['title'], ext='csv')
            csv_zip.write(options['csv_path'], csv_name)

    return zip_name, zip_path, CSV_CONTENT_TYPE


def __prepare_xlsx(csv_options, filename):
    wb = Workbook(write_only=True, iso_dates=True)
    for options in csv_options.values():
        ws = wb.create_sheet(options['title'])
        with open(options['csv_path'], newline='') as f:
            reader = csv.reader(f, delimiter=CSV_SEPARATOR)
            for line in reader:
                ws.append(line)

    xlsx_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='xlsx')
    xlsx_path = EXPORT_DIR + '/' + xlsx_name
    wb.save(xlsx_path)
    wb.close()

    return xlsx_name, xlsx_path, XLSX_CONTENT_TYPE


#
# Parses data and includes them in the csv files.
#
# Steps per data row:
#   1. Flatten the row into a one level object with it’s path as key.
#   2. Identifies row attributes, key name starts with "@".
#   3. If one of the row keys contains an array, instead of flatten it
#      creates a new csv group and includes there the array entries
#      (including the row attributes in each one) as rows.
#
# @param {list}  data    - raw data
# @param {list}  paths   - the list of allowed paths
# @param {dict}  labels  - a dictionary with headers labels
#
def __generate_csv_files(data, paths, labels, offset=0, limit=MAX_SIZE):
    def add_header(options, header):
        if header not in options['headers']:
            options['headers'].append(header)
            options['headers_label'].append(__get_label(header, labels))

    def append_entry(options, entry):
        options['csv_file'].writerow([entry.get(header, '') for header in options.get('headers')])

    def get_current_options(group):
        if group not in csv_options:
            title = '#' if group == '$' else f'#-{len(csv_options.keys())}'
            csv_path = f'{EXPORT_DIR}/temp-{title}.csv'
            f = open(csv_path, 'w', newline='')
            c = csv.writer(f, delimiter=CSV_SEPARATOR)

            csv_options[group] = {
                'file': f,
                'csv_path': csv_path,
                'csv_file': c,
                'title': title,
                'headers': [],
                'headers_label': [],
            }
        return csv_options.get(group)

    def get_full_key(key, group):
        return key if group == '$' else f'{group}.{key}'

    def walker(item, group):
        current = get_current_options(group)

        attrs = [k for k in item.keys() if k.startswith('@')]
        non_attrs = [k for k in item.keys() if not k.startswith('@')]

        # @attributes
        attributes = {}
        for key in attrs:
            value = item[key]
            add_header(current, key)
            attributes[key] = value

        entry = {**attributes}

        # non attributes
        for key in non_attrs:
            value = item[key]
            full_key = get_full_key(key, group)

            if not isinstance(value, list):
                add_header(current, full_key)
                entry[full_key] = value

            else:
                # create array group and walk array elements in it
                array_group = f'{full_key}.{ARRAY_PATH}'
                for i, val in enumerate(value):
                    obj = __flatten_dict(val if isinstance(val, dict) else {'value': val})
                    element = {
                        **attributes,           # identifies the parent
                        f'@.{array_group}': i,  # identifies the element
                        **obj,
                    }
                    walker(element, array_group)

        append_entry(current, entry)

    # start generation
    csv_options = {}
    paths = __filter_paths(paths)

    # paginate results to reduce memory usage
    data_from = offset
    index = offset + 1
    while data_from < limit:
        data_to = min(data_from + PAGE_SIZE, limit)
        for row in data[data_from:data_to]:
            json_data = __parse_row(row.get('exporter_data'), paths)
            walker({'@': index, '@id': str(row.get('pk')), **json_data}, '$')
            index += 1
        data_from = data_to

    # include real headers
    for group in csv_options.keys():
        current = csv_options[group]
        current['file'].close()
        del current['file']

        title = current['title']
        csv_path = f'{EXPORT_DIR}/{title}.csv'
        rows_path = current['csv_path']
        current['csv_path'] = csv_path

        with open(rows_path, newline='') as fr, open(csv_path, 'w', newline='') as fw:
            r = csv.reader(fr)
            w = csv.writer(fw)
            w.writerow(current['headers_label'])
            w.writerows(r)

    return csv_options


def __flatten_dict(obj):
    def _items():
        for key, value in obj.items():
            if isinstance(value, dict):
                for subkey, subvalue in __flatten_dict(value).items():
                    yield key + '.' + subkey, subvalue
            else:
                yield key, value
    return dict(_items())


def __parse_row(row, paths):
    flatten_row = __flatten_dict(row)
    if not paths:
        return flatten_row

    new_row = {}
    for path in paths:
        for key in flatten_row.keys():
            if key == path or key.startswith(path + '.'):
                new_row[key] = flatten_row[key]

    return new_row


def __filter_paths(paths):
    filtered_paths = [
        path
        for path in paths
        if (
            # remove attributes
            not path.startswith('@') and
            # remove xForm internal fields
            path not in ['_id', '_version', 'starttime', 'endtime', 'deviceid', 'meta'] and
            not path.startswith('meta.') and
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


def __get_label(jsonpath, labels={}):
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
    return ' / '.join([get_single('.'.join(pieces[:i + 1])) for i in range(len(pieces))])
