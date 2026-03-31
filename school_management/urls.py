from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import render

handler404 = 'core.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App-Specific URLs
     # Home/Dashboard
    path('students/', include('students.urls')),
    path('finance/', include('finance.urls')),
    path('academic/', include('academic.urls')),
   
    
    # Auth (Login/Logout)
    path('', include('core.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# # Serving media/static files during development
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


