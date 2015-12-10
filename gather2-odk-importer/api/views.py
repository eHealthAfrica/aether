from django.views.generic import View, FormView
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import timezone
from django.db.models.query import EmptyQuerySet
from django.http import HttpResponse

from api import forms as api_forms
from api.auth_utils import AuthService, HttpResponseNotAuthorised
from api.models import XForm


class XFormManifestView(View):

    """
    Return manifest for the XForm
    """

    http_method_names = ["get", ]

    def get(self, *args, **kwargs):
        # TODO fetch the XForm when the manifest is not blank
        # xform = get_object_or_404(
        #     XForm,
        #     id_string=kwargs.get("id_string"),
        #     username=kwargs.get("username")
        # )

        response = render_to_response("xformsManifest.xml", {
            'host': self.request.build_absolute_uri().replace(
                self.request.get_full_path(), ''),
            # TODO do not use an empty query set when we support attachments
            'media_files': EmptyQuerySet
        }, content_type="text/xml; charset=utf-8")

        response['X-OpenRosa-Version'] = '1.0'

        dt = timezone.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        response['Date'] = dt
        return response


class XFormListView(View):

    """
    return a list of forms
    """

    http_method_names = ["get", ]

    def get(self, *args, **kwargs):
        if not AuthService().authorise(username='test', password='test'):
            return HttpResponseNotAuthorised()

        xforms = XForm.objects.filter(username=kwargs.get('username'))

        response = render_to_response('xformsList.xml', {
            'host': self.request.build_absolute_uri().replace(
                self.request.get_full_path(), ''),
            'xforms': xforms
        }, content_type='text/xml; charset=utf-8')

        response['X-OpenRosa-Version'] = '1.0'
        dt = timezone.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        response['Date'] = dt
        return response


class XFormCreateView(FormView):

    """
    receive and XForm and store it in the database
    """

    template_name = 'create_xform.html'
    form_class = api_forms.XFormCreateForm

    def get(self, *args, **kwargs):
        if not AuthService().authorise(username='test', password='test'):
            return HttpResponseNotAuthorised()
        return super(XFormCreateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if not AuthService().authorise(username='test', password='test'):
            return HttpResponseNotAuthorised()
        return super(XFormCreateView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(XFormCreateView, self).get_context_data(*args, **kwargs)
        ctx['username'] = kwargs.get('username')
        return ctx

    def get_initial(self):
        # we want the username back in the form so that we can save it against
        # the model, we do not want to do the auth here in the odk_importer so
        # the easiest way is a hidden field on the form so it can be accessed
        # in the form_valid method
        initial = super(XFormCreateView, self).get_initial()
        initial['username'] = self.kwargs.get('username')
        return initial

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        form_title = form.cleaned_data.get('title')
        form_description = form.cleaned_data.get('description')

        xml_file = form.cleaned_data.get("xml_file")
        xml_contents = xml_file.read()

        xform = XForm(
            username=username,
            title=form_title,
            description=form_description,
            xml_data=xml_contents
        )
        xform.save()

        return super(XFormCreateView, self).form_valid(form)

    def get_success_url(self):
        username = self.kwargs.get('username')
        return reverse('xformcreate', kwargs={'username': username})


class XFormXMLView(View):

    """
    return a single form in XML format
    """

    http_method_names = ["get", ]

    def get(self, *args, **kwargs):
        username = kwargs.get("username")

        if not AuthService().authorise(username='test', password='test'):
            return HttpResponseNotAuthorised()

        pk = kwargs.get("pk")

        xform = get_object_or_404(
            XForm,
            username=username,
            pk=pk
        )

        response = HttpResponse(
            xform.xml_data,
            content_type="text/xml; charset=utf-8"
        )
        response['X-OpenRosa-Version'] = '1.0'
        return response
