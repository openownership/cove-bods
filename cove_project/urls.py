from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from cove.urls import urlpatterns as urlpatterns_core

import cove_bods.views


# Serve the OCDS validator at /validator/
urlpatterns_core += [url(r'^data/(.+)$', cove_bods.views.explore_bods, name='explore')]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='review/', permanent=False)),
    url('^validator/', include(urlpatterns_core)),
    url('^review/', include(urlpatterns_core)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
