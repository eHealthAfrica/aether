from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from aether.common.conf.urls import generate_urlpatterns

# Any entry here needs the decorator `tokens_required` if it's going to execute
# AJAX request to any of the other apps
from .api.decorators import tokens_required
from .api.views import empty


urlpatterns = generate_urlpatterns(kernel=True) + [

    # ----------------------
    # API
    path('', include('gather.api.urls', namespace='gather')),
    path('v1/', include('gather.api.urls', namespace='v1')),

    # ----------------------
    # Welcome page
    path('',
         login_required(TemplateView.as_view(template_name='pages/index.html')),
         name='index-page'),

    # ----------------------
    # shows the current user app tokens
    path('~tokens',
         login_required(TemplateView.as_view(template_name='pages/tokens.html')),
         name='tokens'),
    # to check if the user tokens are valid
    path('check-tokens', login_required(tokens_required(empty)), name='check-tokens'),

    re_path(r'^surveys/(?P<action>\w+)/(?P<survey_id>[0-9a-f-]+)?$',
            login_required(tokens_required(TemplateView.as_view(template_name='pages/surveys.html'))),
            name='surveys'),
]

if settings.AETHER_ODK:  # pragma: no cover
    urlpatterns += [
        re_path(r'^surveyors/(?P<action>\w+)/(?P<surveyor_id>[0-9]+)?$',
                login_required(tokens_required(TemplateView.as_view(template_name='pages/surveyors.html'))),
                name='surveyors'),
    ]
