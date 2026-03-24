from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App-Specific URLs
    path('', include('core.urls')), # Home/Dashboard
    path('students/', include('students.urls')),
    path('finance/', include('finance.urls')),
    path('academic/', include('academic.urls')),
    
    # Auth (Login/Logout)
    path('accounts/', include('django.contrib.auth.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serving media/static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)