from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.views.generic import TemplateView

from aether.common.conf.urls import generate_urlpatterns

# Any entry here needs the decorator `tokens_required` if it's going to execute
# AJAX request to any of the other apps
from .api.decorators import tokens_required
from .api.views import empty


urlpatterns = generate_urlpatterns(kernel=True) + [
    # API
    url(r'^/', include('ui.api.urls', namespace='ui')),
    url(r'^v1/', include('ui.api.urls', namespace='v1')),
    # Welcome page
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='index-page'),
    # shows the current user app tokens
    url(r'^~tokens$',
        login_required(TemplateView.as_view(template_name='pages/tokens.html')),
        name='tokens'),
    # to check if the user tokens are valid
    url(r'^check-tokens$', login_required(tokens_required(empty)), name='check-tokens'),
]
