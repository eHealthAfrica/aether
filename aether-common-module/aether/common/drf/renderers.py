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

from rest_framework_csv.renderers import CSVStreamingRenderer


class CustomCSVRenderer(CSVStreamingRenderer):
    # https://github.com/mjumbewu/django-rest-framework-csv#pagination
    results_field = 'results'

    values_sep_param = 'columns_sep'

    # use to filter out the csv columns
    headers_param = 'columns'
    headers_key = 'header'

    # use to generate custom header labels
    labels_rule_sep_param = 'rule_sep'
    labels_param = 'parse_columns'
    labels_key = 'labels'

    def render(self, data, media_type=None, renderer_context={}, *args, **kwargs):
        if data is None:
            return ''

        # extract data from paginated object
        if not isinstance(data, list):
            data = data.get(self.results_field, [])

        # dynamic csv header
        request = renderer_context['request']

        csv_header = self.__get_param(request, self.headers_param)
        if csv_header:
            header_fields = self.__extract_headers(data)

            # use CSV headers to filter the valid header fields
            filtered_headers = []
            for header in header_fields:
                for prefix in csv_header:
                    # search this header in the csv header prefixes
                    if header.startswith(prefix):
                        filtered_headers.append(header)

            # pass filtered headers to context
            renderer_context[self.headers_key] = filtered_headers

        # create custom labels for headers
        label_rules = self.__get_param(request, self.labels_param)
        if label_rules:
            # create the header labels
            if self.headers_key not in renderer_context:
                renderer_context[self.headers_key] = self.__extract_headers(data)

            # "label_rules" is a list of rules to generate header labels
            labels = {}
            for header in renderer_context[self.headers_key]:
                # create entry for this header
                labels[header] = apply_label_rules(
                    rules=label_rules,
                    value=header,
                    rule_sep=self.__get(request, self.labels_rule_sep_param, ':'),
                )

            # pass header labels to context
            renderer_context[self.labels_key] = labels

        return super(CustomCSVRenderer, self).render(
            data, media_type, renderer_context, *args, **kwargs)

    def __get(self, request, name, default=None):
        return request.GET.get(name, dict(request.data).get(name, default))

    def __get_param(self, request, param_name):
        return (
            self.__get(request, param_name).split(self.__get(request, self.values_sep_param, ','))
            if self.__get(request, param_name) else None)

    def __extract_headers(self, data):
        # First, flatten the data
        csv_data = self.flatten_data(data)

        # Get the set of all unique headers.
        header_fields = set()
        for item in tuple(csv_data):
            header_fields.update(list(item.keys()))
        return sorted(header_fields)


def apply_label_rules(rules, value, rule_sep=':'):
    initial_value = value
    try:
        # transforms the value following the indicating rules in ORDER!!!
        for rule in rules:
            value = apply_label_rule(rule, value, rule_sep)
        return value
    except Exception:
        # if one of the parsing rules fails return initial value
        return initial_value


def apply_label_rule(rule, value, rule_sep=':'):

    if rule == 'lower':
        return value.lower()

    if rule == 'upper':
        return value.upper()

    if rule == 'title':
        return value.title()

    if rule == 'capitalize':
        return value.capitalize()

    rule_name = f'remove-prefix{rule_sep}'
    if rule.startswith(rule_name) and rule != rule_name:
        prefix = rule.split(rule_sep)[1]
        if value.startswith(prefix):
            return value[len(prefix):]
        return value

    rule_name = f'remove-suffix{rule_sep}'
    if rule.startswith(rule_name) and rule != rule_name:
        suffix = rule.split(rule_sep)[1]
        if value.endswith(suffix):
            return value[:-len(suffix)]
        return value

    rule_name = f'replace{rule_sep}'
    if rule.startswith(rule_name) and rule != rule_name:
        old_sep = rule.split(rule_sep)[1]
        new_sep = rule.split(rule_sep)[2]
        return value.replace(old_sep, new_sep)

    rule_name = f'split{rule_sep}'
    if rule.startswith(rule_name) and rule != rule_name:
        # replaces the separator with spaces
        # shortcut of `replace:<sep>: `
        sep = rule.split(rule_sep)[1]
        return value.replace(sep, ' ')

    return value
