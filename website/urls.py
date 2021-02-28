from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('', include('accounts.urls')),
    path('', include('complaints.urls')),
    path('', include('incidents.urls')),
    path('', include('chatapp.urls')),
    path('', include('adminconsole.urls')),
    path('', include('cyberbullying.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
