# streaming/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    
    # Watch endpoint for getting movie details with streaming links
    path('api/watch/<str:imdb_id>/', views.MovieWatchView.as_view(), name='movie-watch'),
    
    # NEW: Proxy player route (bypasses referrer restrictions)
    path('player/<str:imdb_id>/<int:link_id>/', views.player_proxy, name='player-proxy'),
]