"""
This urls are only used for testing purposes.

The app that includes this module should have its own urls list.
"""

from aether.common.conf.urls import generate_urlpatterns

urlpatterns = generate_urlpatterns(kernel=True, token=True)
