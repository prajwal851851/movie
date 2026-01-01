# streaming/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')
router.register(r'watchlist', views.UserWatchlistViewSet, basename='watchlist')
router.register(r'favorites', views.UserFavoriteViewSet, basename='favorite')
router.register(r'history', views.WatchHistoryViewSet, basename='history')
router.register(r'reviews', views.ReviewViewSet, basename='review')


urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    
    # Watch endpoint
    path('api/watch/<str:imdb_id>/', views.MovieWatchView.as_view(), name='movie-watch'),
    
    # Proxy player route (CRITICAL for Luluvdo, Dood, and other problematic servers)
    path('player/<str:imdb_id>/<int:link_id>/', views.player_proxy, name='player-proxy'),
    
    # Video extraction and proxying endpoints
    path('api/extract-video/', views.extract_video_url, name='extract_video'),
    path('api/proxy-video/', views.proxy_video, name='proxy_video'),
]