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
from .avro_tools import ARRAY_PATH, MAP_PATH, UNION_PATH

EXPORT_DIR = tempfile.mkdtemp()
FILENAME_RE = '{name}-{ts}.{ext}'

CSV_CONTENT_TYPE = 'application/zip'
XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def export_data(data, paths=[], headers={}, format='xlsx', filename='export', **kwargs):
    '''
    Generates an XLSX/ ZIP (of CSV files) file with the given data.

    - ``data`` is a list of dictionaries with two keys ``id`` and ``payload``.
    - ``paths`` is a list with the allowed payload jsonpaths.
    - ``headers`` is a dictionary which keys are the payload jsonpaths
      and the values the linked labels to use as header for that jsonpath.
    - ``format``, expected values ``xlsx`` (default) and ``csv``.
    '''

    # create workbook
    wb = __generate_workbook(paths=paths, labels=headers, data=data)

    xlsx_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='xlsx')
    xlsx_path = EXPORT_DIR + '/' + xlsx_name
    wb.save(xlsx_path)
    wb.close()

    if format == 'csv':
        return export_csv(xlsx_path, filename, kwargs.get('separator', ','))
    else:
        return __file_response(
            filepath=xlsx_path,
            filename=xlsx_name,
            content_type=XLSX_CONTENT_TYPE,
        )


def export_csv(wb_path, filename, separator=','):
    # convert XLSX file into several CSV files and return zip file
    zip_name = FILENAME_RE.format(name=filename, ts=datetime.now().isoformat(), ext='zip')
    zip_path = EXPORT_DIR + '/' + filename
    with zipfile.ZipFile(zip_path, 'w') as myzip:
        wb = load_workbook(filename=wb_path, read_only=True)
        for ws in wb.worksheets:
            csv_name = FILENAME_RE.format(name=filename, ts=ws.title, ext='csv')
            csv_path = EXPORT_DIR + '/' + csv_name

            with open(csv_path, 'w', newline='') as f:
                c = csv.writer(f, delimiter=separator)
                for row in ws.rows:
                    c.writerow([cell.value or '' for cell in row])
            # include csv file in zip
            myzip.write(csv_path, csv_name)
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
def __generate_workbook(paths, labels, data):
    def add_header(options, header):
        if header not in options['headers']:
            options['current_header'] += 1
            col = options['current_header']
            options['headers'].append(header)
            options['ws'].cell(row=1, column=col).value = __get_label(header, labels)

    def get_current_options(group):
        if group not in skeleton:
            skeleton[group] = {
                'ws': wb.create_sheet('#'),
                'headers': [],
                'current_header': 0,
                'current_row': 1,  # the first row is the header
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
        current['current_row'] += 1
        for i, header in enumerate(current['headers']):
            current['ws'].cell(row=current['current_row'], column=i + 1).value = entry.get(header, '')

    # create workbook
    wb = Workbook()
    ws_default = wb.active
    skeleton = {}
    paths = __filter_paths(paths)

    for row in data:
        # filter row payload by given paths
        payload = __parse_row(row['payload'], paths)
        # include data in workbook
        walker({'@id': str(row['id']), **payload}, '$')

    # remove first Sheet (added automatically when the workbook was created)
    wb.remove(ws_default)
    return wb


def __flatten_dict(obj):
    def flatten_item(item):
        if isinstance(item, dict):
            return __flatten_dict(item)
        else:
            return {'': item}

    flat_dict = {}
    for key, item in obj.items():
        flat_item = flatten_item(item)

        nested_item = {}
        for k, v in flat_item.items():
            nested_key = '.'.join([key, k]) if k else key
            nested_item[nested_key] = v

        flat_dict.update(nested_item)
    return flat_dict


def __parse_row(row, paths):
    flatten_row = __flatten_dict(row)
    if not paths:
        return flatten_row

    payload = {}
    for path in paths:
        for key in flatten_row.keys():
            if key == path or key.startswith(path + '.'):
                payload[key] = flatten_row[key]

    return payload


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
