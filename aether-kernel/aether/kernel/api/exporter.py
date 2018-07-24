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

from openpyxl import Workbook, load_workbook

from django.http import FileResponse
from django.db.models import F
from django.utils.translation import ugettext as _

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action

from .avro_tools import ARRAY_PATH, MAP_PATH, UNION_PATH, extract_jsonpaths_and_docs

EXPORT_DIR = tempfile.mkdtemp()
FILENAME_RE = '{name}-{ts}.{ext}'

CSV_CONTENT_TYPE = 'application/zip'
XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# Total number of rows on a worksheet (since Excel 2007): 1048576
# https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3
MAX_SIZE = 1048575  # the missing one is the header


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
        separator = self.__get(request, 'separator', ',')
        return self.__export(request, format='csv', separator=separator)

    def __get(self, request, name, default=None):
        return request.GET.get(name, dict(request.data).get(name, default))

    def __export(self, request, format, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = queryset.annotate(exporter_data=F(self.json_field))

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
            return export_data(
                data=data,
                paths=jsonpaths,
                headers=docs,
                format=format,
                filename=self.__get(request, 'filename', 'export'),
                offset=offset,
                limit=limit,
                **kwargs
            )

        except IOError as e:
            msg = _('Got an error while creating the file: {error}').format(error=str(e))
            return Response(data={'detail': msg}, status=500)


def export_data(data,
                paths=[],
                headers={},
                format='xlsx',
                filename='export',
                offset=0,
                limit=MAX_SIZE,
                **kwargs
                ):
    '''
    Generates an XLSX/ ZIP (of CSV files) file with the given data.

    - ``data`` is a queryset with two main properties ``pk`` and ``exporter_data``.
    - ``paths`` is a list with the allowed jsonpaths.
    - ``headers`` is a dictionary which keys are the jsonpaths
      and the values the linked labels to use as header for that jsonpath.
    - ``format``, expected values ``xlsx`` (default) and ``csv``.
    '''

    # create workbook
    xlsx_path = __generate_workbook(
        paths=paths,
        labels=headers,
        data=data,
        offset=offset,
        limit=limit,
    )

    if format == 'csv':
        return __export_csv(xlsx_path, filename, kwargs.get('separator', ','))
    else:
        xlsx_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='xlsx')
        return __file_response(
            filepath=xlsx_path,
            filename=xlsx_name,
            content_type=XLSX_CONTENT_TYPE,
        )


def __export_csv(wb_path, filename, separator=','):
    # convert XLSX file into several CSV files and return zip file
    zip_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='zip')
    zip_path = EXPORT_DIR + '/' + filename
    with zipfile.ZipFile(zip_path, 'w') as csv_zip:
        wb = load_workbook(filename=wb_path, read_only=True)
        for ws in wb.worksheets:
            csv_name = FILENAME_RE.format(name=filename, ts=ws.title, ext='csv')
            csv_path = EXPORT_DIR + '/' + csv_name

            with open(csv_path, 'w', newline='') as f:
                c = csv.writer(f, delimiter=separator)
                for row in ws.rows:
                    c.writerow([cell.value or '' for cell in row])
            # include csv file in zip
            csv_zip.write(csv_path, csv_name)
        wb.close()

    return __file_response(
        filepath=zip_path,
        filename=zip_name,
        content_type=CSV_CONTENT_TYPE,
    )


def __file_response(filepath, filename, content_type):
    response = FileResponse(open(filepath, 'rb'))
    response['Content-Type'] = content_type
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = os.path.getsize(filepath)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


#
# Parses data and includes them in the workbook object.
#
# Steps per data row:
#   1. Flatten the row into a one level object with it’s path as key.
#   2. Identifies row attributes, key name starts with "@".
#   3. If one of the row keys contains an array, instead of flatten it
#      creates a new group in the skeleton result and includes there
#      the array entries (including the row attributes in each one) as rows.
#
# @param {list}  paths   - the list of allowed paths
# @param {dict}  labels  - a dictionary with headers labels
# @param {list}  data    - raw and flatten data
#
def __generate_workbook(paths, labels, data, offset=0, limit=MAX_SIZE):
    def add_header(options, header):
        if header not in options['headers']:
            options['headers'].append(header)
            options['headers_label'].append(__get_label(header, labels))

    def get_current_options(group):
        if group not in skeleton:
            ws = wb.create_sheet('#')
            ws.append([])  # first row contains the headers, will be written afterwards
            skeleton[group] = {
                'ws': ws,
                'ws_name': ws.title,
                'headers': [],
                'headers_label': [],
            }
        return skeleton.get(group)

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

        # append entry to current worksheet
        current['ws'].append([entry.get(header, '') for header in current.get('headers')])

    skeleton = {}
    paths = __filter_paths(paths)

    # create workbook
    wb = Workbook(write_only=True, iso_dates=True)

    # paginate results to reduce memory usage
    PAGE_SIZE = 500
    data_from = offset
    index = offset + 1
    while data_from < limit:
        data_to = min(data_from + PAGE_SIZE, limit)
        for row in data[data_from:data_to]:
            json_data = __parse_row(row.exporter_data, paths)
            walker({'@': index, '@id': str(row.pk), **json_data}, '$')
            index += 1
        data_from = data_to

    # save it
    xlsx_path = EXPORT_DIR + '/temp.xlsx'
    wb.save(xlsx_path)
    wb.close()

    # open again and include real headers
    wb = load_workbook(filename=xlsx_path)
    for group in skeleton.keys():
        current = skeleton[group]
        ws = wb[current['ws_name']]
        for i, header in enumerate(current['headers_label']):
            ws.cell(row=1, column=i + 1).value = header

    wb.save(xlsx_path)
    wb.close()

    return xlsx_path


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
