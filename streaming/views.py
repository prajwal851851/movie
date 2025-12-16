# streaming/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from .models import Movie
from .serializers import MovieSerializer

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows movies to be viewed.
    """
    queryset = Movie.objects.all().prefetch_related('links')
    serializer_class = MovieSerializer
    lookup_field = 'imdb_id'

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_all(self, request):
        """
        Triggers a full scrape of both target sites.
        POST /api/movies/refresh/
        """
        try:
            # Run both spiders
            call_command('scrape_target', 'makemovies')
            call_command('scrape_target', 'fawesome')
            return Response({"status": "Scraping started for both sites."}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MovieWatchView(APIView):
    """
    A view to handle the logic for the 'watch' page.
    It provides the movie details and its active streaming links.
    """
    def get(self, request, imdb_id):
        movie = get_object_or_404(Movie, imdb_id=imdb_id)
        active_links = movie.links.filter(is_active=True)
        
        if not active_links.exists():
            # If no active links, you could trigger a refresh here,
            # but for simplicity, we'll just return what we have.
            pass

        serializer = MovieSerializer(movie)
        return Response(serializer.data)