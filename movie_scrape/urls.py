# movie_scrape/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main app (serves index.html)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Include all streaming URLs (API + player proxy)
    path('', include('streaming.urls')),
]