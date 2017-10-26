from rest_framework_csv.renderers import CSVRenderer


class CustomCSVRenderer(CSVRenderer):
    results_field = 'results'

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        return super(CustomCSVRenderer, self).render(data, *args, **kwargs)
