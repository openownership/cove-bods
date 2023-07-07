from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from libcoveweb2.urls import urlpatterns
import cove_bods.views
from django.urls import re_path

urlpatterns += [re_path(r"^$", cove_bods.views.NewInput.as_view(), name="index")]
urlpatterns += [url(r'^data/(.+)$', cove_bods.views.ExploreBODSView.as_view(), name='explore')]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler500 = "libcoveweb2.views.handler500"
