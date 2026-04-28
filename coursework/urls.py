from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings

from django.contrib import admin
from django.urls import path,include
from django.views.generic.base import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('users/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
