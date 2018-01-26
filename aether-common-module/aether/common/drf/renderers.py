from rest_framework_csv.renderers import CSVStreamingRenderer


class CustomCSVRenderer(CSVStreamingRenderer):
    # https://github.com/mjumbewu/django-rest-framework-csv#pagination
    results_field = 'results'

    # use to filter out the csv columns
    headers_param = 'columns'
    headers_key = 'header'

    # use to generate custom header labels
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
                labels[header] = apply_label_rules(label_rules, header)

            # pass header labels to context
            renderer_context[self.labels_key] = labels

        return super(CustomCSVRenderer, self).render(
            data, media_type, renderer_context, *args, **kwargs)

    def __get_param(self, request, param_name):
        return (
            request.GET[param_name].split(',')
            if request is not None and param_name in request.GET else None)

    def __extract_headers(self, data):
        # First, flatten the data
        csv_data = self.flatten_data(data)

        # Get the set of all unique headers.
        header_fields = set()
        for item in tuple(csv_data):
            header_fields.update(list(item.keys()))
        return sorted(header_fields)


def apply_label_rules(rules, value):
    initial_value = value
    try:
        # transforms the value following the indicating rules in ORDER!!!
        for rule in rules:
            value = apply_label_rule(rule, value)
        return value
    except Exception as e:
        # if one of the parsing rules fails return initial value
        return initial_value


def apply_label_rule(rule, value):

    if rule == 'lower':
        return value.lower()

    if rule == 'upper':
        return value.upper()

    if rule == 'title':
        return value.title()

    if rule == 'capitalize':
        return value.capitalize()

    if rule.startswith('remove-prefix:') and rule != 'remove-prefix:':
        prefix = rule.split(':')[1]
        if value.startswith(prefix):
            return value[len(prefix):]
        return value

    if rule.startswith('remove-suffix:') and rule != 'remove-suffix:':
        suffix = rule.split(':')[1]
        if value.endswith(suffix):
            return value[:-len(suffix)]
        return value

    if rule.startswith('replace:'):
        old_sep = rule.split(':')[1]
        new_sep = rule.split(':')[2]
        return value.replace(old_sep, new_sep)

    if rule.startswith('split:') and rule != 'split:':
        # replaces the separator with spaces
        sep = rule.split(':')[1]
        return value.replace(sep, ' ')

    return value
