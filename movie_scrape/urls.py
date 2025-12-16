# movie_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from streaming import views
from django.shortcuts import render # Add this import

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/watch/<str:imdb_id>/', views.MovieWatchView.as_view(), name='movie-watch'),
    path('', lambda request: render(request, 'index.html'), name='frontend'), # Add this path
]