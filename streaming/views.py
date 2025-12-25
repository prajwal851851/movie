# streaming/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .pagination import CursorPaginationExample
from django.core.management import call_command
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.db import models
from .models import Movie
from .serializers import MovieSerializer
import threading
import urllib.parse


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows movies to be viewed.
    """
    queryset = Movie.objects.all().prefetch_related('links')
    serializer_class = MovieSerializer
    lookup_field = 'imdb_id'
    pagination_class = CursorPaginationExample
    
    def get_queryset(self):
        """Filter by content_type, search, and year if provided"""
        queryset = Movie.objects.all().prefetch_related('links')
        content_type = self.request.query_params.get('content_type')
        search = self.request.query_params.get('search')
        year = self.request.query_params.get('year')

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        if search:
            # Search in title and synopsis
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(synopsis__icontains=search)
            )

        if year:
            queryset = queryset.filter(year=year)

        return queryset

    

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

    @action(detail=False, methods=['get'], url_path='years')
    def years(self, request):
        """
        Get distinct years from movies and series.
        GET /api/movies/years/
        """
        years = Movie.objects.exclude(year__isnull=True).values_list('year', flat=True).distinct().order_by('-year')
        return Response(list(years))

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


# ADD THIS FUNCTION AT THE END
def player_proxy(request, imdb_id, link_id):
    """
    Proxy page that loads the embed in a clean environment
    This bypasses referrer restrictions from VideoStr.net
    """
    try:
        movie = Movie.objects.get(imdb_id=imdb_id)
        link = movie.links.filter(id=link_id, is_active=True).first()
        
        if not link:
            return HttpResponse("Link not found or inactive", status=404)
        
        # Create a clean HTML page that loads the embed
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="referrer" content="no-referrer">
    <title>{movie.title}</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100vh;
            overflow: hidden;
            background: #000;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-family: Arial;
            text-align: center;
        }}
        .spinner {{
            border: 4px solid #333;
            border-top: 4px solid #e50914;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <p>Loading {movie.title}...</p>
        <p style="font-size: 0.9em; color: #888;">Server: {link.server_name}</p>
    </div>
    <iframe 
        src="{link.stream_url}" 
        allowfullscreen
        allow="autoplay; fullscreen; picture-in-picture"
        sandbox="allow-forms allow-scripts allow-same-origin allow-presentation"
        referrerpolicy="no-referrer">
    </iframe>
    <script>
        // Remove loading message after iframe loads
        const iframe = document.querySelector('iframe');
        iframe.onload = function() {{
            setTimeout(() => {{
                document.querySelector('.loading').style.display = 'none';
            }}, 1500);
        }};
        
        // Fallback: hide loading after 3 seconds even if onload doesn't fire
        setTimeout(() => {{
            document.querySelector('.loading').style.display = 'none';
        }}, 3000);
    </script>
</body>
</html>
        """
        return HttpResponse(html)
        
    except Movie.DoesNotExist:
        return HttpResponse("Movie not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


# streaming/views.py
# Add these imports at the top
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import re
from urllib.parse import urlparse, urljoin

# Add this new view to handle video extraction
@require_http_methods(["GET"])
def extract_video_url(request):
    """
    Extract actual video URL from embed services
    This endpoint takes an embed URL and returns the direct video URL
    """
    embed_url = request.GET.get('url')
    
    if not embed_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)
    
    try:
        # Make request to embed page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://sflix.ps/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(embed_url, headers=headers, timeout=10)
        html = response.text
        
        # Method 1: Look for M3U8 URLs (HLS streams)
        m3u8_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
        m3u8_matches = re.findall(m3u8_pattern, html)
        
        if m3u8_matches:
            video_url = m3u8_matches[0]
            return JsonResponse({
                'success': True,
                'video_url': video_url,
                'type': 'm3u8',
                'message': 'Found HLS stream'
            })
        
        # Method 2: Look for MP4 URLs
        mp4_pattern = r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)'
        mp4_matches = re.findall(mp4_pattern, html)
        
        if mp4_matches:
            video_url = mp4_matches[0]
            return JsonResponse({
                'success': True,
                'video_url': video_url,
                'type': 'mp4',
                'message': 'Found MP4 stream'
            })
        
        # Method 3: Look for common video player configurations
        video_patterns = [
            r'"file"\s*:\s*"([^"]+)"',
            r'"src"\s*:\s*"([^"]+)"',
            r'"url"\s*:\s*"([^"]+)"',
            r'source\s*:\s*"([^"]+)"',
            r'sources\s*:\s*\[.*?"src"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if match and ('m3u8' in match or 'mp4' in match):
                    return JsonResponse({
                        'success': True,
                        'video_url': match,
                        'type': 'extracted',
                        'message': 'Found video URL in player config'
                    })
        
        # Method 4: Return embed URL with special handling flag
        return JsonResponse({
            'success': True,
            'video_url': embed_url,
            'type': 'embed',
            'message': 'Using embed URL (direct extraction failed)',
            'requires_proxy': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'video_url': embed_url,
            'type': 'fallback'
        }, status=500)


@require_http_methods(["GET"])
def proxy_video(request):
    """
    Proxy video streams to avoid CORS issues
    """
    video_url = request.GET.get('url')
    
    if not video_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://sflix.ps/',
            'Origin': 'https://sflix.ps',
        }
        
        # Stream the video content
        response = requests.get(video_url, headers=headers, stream=True, timeout=10)
        
        # Create Django response with video content
        django_response = HttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('content-type', 'video/mp4')
        )
        
        # Copy relevant headers
        for header in ['Content-Length', 'Accept-Ranges', 'Content-Range']:
            if header in response.headers:
                django_response[header] = response.headers[header]
        
        return django_response
        
    except Exception as e:
        return HttpResponse(f'Error proxying video: {str(e)}', status=500)


# Add to your existing watch view
def watch_movie(request, imdb_id):
    """Enhanced watch view with video URL extraction"""
    try:
        movie = Movie.objects.get(imdb_id=imdb_id)
        links = movie.streaming_links.filter(is_active=True)
        
        links_data = []
        for link in links:
            link_data = {
                'stream_url': link.stream_url,
                'server_name': link.server_name,
                'quality': link.quality,
                'language': link.language,
                'is_active': link.is_active,
                # Add flag to indicate if video extraction is needed
                'needs_extraction': not any(ext in link.stream_url.lower() 
                                          for ext in ['.m3u8', '.mp4', '.mkv'])
            }
            links_data.append(link_data)
        
        return JsonResponse({
            'movie': {
                'title': movie.title,
                'year': movie.year,
                'synopsis': movie.synopsis,
                'poster_url': movie.poster_url,
            },
            'links': links_data
        })
    except Movie.DoesNotExist:
        return JsonResponse({'error': 'Movie not found'}, status=404)


# Don't forget to add these URLs to your urls.py:
"""
from streaming.views import extract_video_url, proxy_video, watch_movie

urlpatterns = [
    path('api/extract-video/', extract_video_url, name='extract_video'),
    path('api/proxy-video/', proxy_video, name='proxy_video'),
    path('api/watch/<str:imdb_id>/', watch_movie, name='watch_movie'),
    # ... other patterns
]
"""