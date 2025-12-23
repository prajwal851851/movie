# streaming/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from .models import Movie
from .serializers import MovieSerializer
import threading

class MovieCursorPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows movies to be viewed.
    """
    queryset = Movie.objects.all().prefetch_related('links')
    serializer_class = MovieSerializer
    lookup_field = 'imdb_id'
    pagination_class = MovieCursorPagination

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_all(self, request):
        """
        Triggers a full scrape of all target sites.
        POST /api/movies/refresh/
        """
        try:
            # Run scraping in a background thread to avoid timeout
            def run_scrapers():
                try:
                    call_command('scrape_all_sites', sites=['movietreasures', 'fmovies'])
                except Exception as e:
                    print(f"Error in background scraping: {e}")
            
            thread = threading.Thread(target=run_scrapers)
            thread.daemon = True
            thread.start()
            
            return Response({
                "status": "Scraping started for all sites.",
                "message": "This process runs in the background. Check back in a few minutes."
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='refresh-site')
    def refresh_site(self, request):
        """
        Triggers a scrape of a specific site.
        POST /api/movies/refresh-site/
        Body: {"site": "movietreasures"} or {"site": "fmovies"}
        """
        site = request.data.get('site')
        
        valid_sites = ['movietreasures', 'fmovies', 'makemovies', 'simple_movies']
        if site not in valid_sites:
            return Response({
                "error": f"Invalid site. Choose from: {', '.join(valid_sites)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            def run_scraper():
                try:
                    call_command('scrape_target', site)
                except Exception as e:
                    print(f"Error in background scraping: {e}")
            
            thread = threading.Thread(target=run_scraper)
            thread.daemon = True
            thread.start()
            
            return Response({
                "status": f"Scraping started for {site}.",
                "message": "This process runs in the background. Check back in a few minutes."
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get statistics about the movie database.
        GET /api/movies/stats/
        """
        from django.db.models import Count
        
        stats = {
            'total_movies': Movie.objects.count(),
            'movies_by_site': dict(
                Movie.objects.values('source_site')
                .annotate(count=Count('source_site'))
                .values_list('source_site', 'count')
            ),
            'movies_with_links': Movie.objects.filter(links__isnull=False).distinct().count(),
            'total_streaming_links': Movie.objects.values('links').distinct().count(),
        }
        
        return Response(stats)

class MovieWatchView(APIView):
    """
    A view to handle the logic for the 'watch' page.
    It provides the movie details and its active streaming links.
    """
    def get(self, request, imdb_id):
        movie = get_object_or_404(Movie, imdb_id=imdb_id)
        active_links = movie.links.filter(is_active=True)
        
        if not active_links.exists():
            # No active links available
            pass

        serializer = MovieSerializer(movie)
        return Response(serializer.data)