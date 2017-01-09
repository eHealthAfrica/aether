from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter


class TemplateRouter(DefaultRouter):

    def __init__(self, template_name, *args, **kwargs):
        self.template_name = template_name
        super(TemplateRouter, self).__init__(*args, **kwargs)

    def get_api_root_view(self, *args, **kwargs):
        view = super(TemplateRouter, self).get_api_root_view(*args, **kwargs)

        def view_wrapper(*args, **kwargs):
            resp = view(*args, **kwargs)
            resp.template_name = self.template_name
            return resp

        return view_wrapper
