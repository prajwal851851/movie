# movie_scrape/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main app - React StreamFlix UI
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Old UI (for reference/backup)
    path('old/', TemplateView.as_view(template_name='index_old.html'), name='old-home'),
    
    # Include all streaming URLs (API + player proxy)
    path('', include('streaming.urls')),
    
    # Auth API
    path('api/auth/', include('users.urls')),
]