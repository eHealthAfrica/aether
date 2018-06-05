from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(kernel=True) + [
    # API
    url(r'^api/', include('aether.ui.api.urls')),

    # Pipeline builder app
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/pipeline.html')),
        name='pipeline-app'),

    # styleguide
    url(r'^styleguide/',
        login_required(TemplateView.as_view(template_name='pages/styleguide.html')),
        name='styleguide'),
]
