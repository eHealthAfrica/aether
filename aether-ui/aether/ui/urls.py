from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.views.generic import TemplateView

from aether.common.conf.urls import generate_urlpatterns
from aether.common.health.views import health

# Any entry here needs the decorator `tokens_required` if it's going to execute
# AJAX request to any of the other apps
from .api.decorators import tokens_required


urlpatterns = generate_urlpatterns(kernel=True) + [
    # API
    url(r'^api/', include('aether.ui.api.urls', namespace='ui')),

    # shows the current user app tokens
    url(r'^~tokens$',
        login_required(TemplateView.as_view(template_name='pages/tokens.html')),
        name='tokens'),

    # to check if the user tokens are valid
    url(r'^check-tokens$', login_required(tokens_required(health)), name='check-tokens'),

    # Pipeline builder app
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/pipeline.html')),
        name='pipeline-app'),

    # styleguide
    url(r'^styleguide/',
         login_required(TemplateView.as_view(template_name='pages/styleguide.html')),
         name='styleguide'),
]
