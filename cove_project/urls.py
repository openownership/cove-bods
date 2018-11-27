from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from cove.urls import urlpatterns
import cove_bods.views

urlpatterns += [url(r'^data/(.+)$', cove_bods.views.explore_bods, name='explore')]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
