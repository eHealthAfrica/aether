from rest_framework_csv.renderers import CSVStreamingRenderer


class CustomCSVRenderer(CSVStreamingRenderer):
    # https://github.com/mjumbewu/django-rest-framework-csv#pagination
    results_field = 'results'

    # use to filter out the csv columns
    headers_param = 'columns'

    def render(self, data, media_type=None, renderer_context={}, *args, **kwargs):
        if data is None:
            return ''

        # extract data from paginated object
        if not isinstance(data, list):
            data = data.get(self.results_field, [])

        # dynamic csv header
        request = renderer_context['request']
        csv_header = (
            request.GET[self.headers_param].split(',')
            if request is not None and self.headers_param in request.GET else None)
        if csv_header:
            # First, flatten the data
            csv_data = self.flatten_data(data)

            # Get the set of all unique headers.
            header_fields = set()
            for item in tuple(csv_data):
                header_fields.update(list(item.keys()))
            header_fields = sorted(header_fields)

            # use CSV headers to filter the valid header fields
            filtered_headers = []
            for header in header_fields:
                for prefix in csv_header:
                    # search this header in the csv header prefixes
                    if header.startswith(prefix):
                        filtered_headers.append(header)

            # pass filtered headers to context
            renderer_context['header'] = filtered_headers

        return super(CustomCSVRenderer, self).render(
            data, media_type, renderer_context, *args, **kwargs)
