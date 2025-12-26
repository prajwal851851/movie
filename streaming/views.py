# streaming/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .pagination import CursorPaginationExample
from django.core.management import call_command
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
from .models import Movie, StreamingLink
from .serializers import MovieSerializer
import threading
import urllib.parse
import requests
import re


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all().prefetch_related('links')
    serializer_class = MovieSerializer
    lookup_field = 'imdb_id'
    pagination_class = CursorPaginationExample
    
    def get_queryset(self):
        queryset = Movie.objects.all().prefetch_related('links')
        content_type = self.request.query_params.get('content_type')
        search = self.request.query_params.get('search')
        year = self.request.query_params.get('year')

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(synopsis__icontains=search)
            )

        if year:
            queryset = queryset.filter(year=year)

        return queryset

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_all(self, request):
        try:
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
        years = Movie.objects.exclude(year__isnull=True).values_list('year', flat=True).distinct().order_by('-year')
        return Response(list(years))


class MovieWatchView(APIView):
    """Enhanced watch view that marks problematic servers for proxy usage"""
    
    def get(self, request, imdb_id):
        movie = get_object_or_404(Movie, imdb_id=imdb_id)
        serializer = MovieSerializer(movie)
        data = serializer.data
        
        # Domains that MUST use proxy due to X-Frame-Options or other restrictions
        PROXY_DOMAINS = [
            'luluvdo.com',
            'dood',
            'mixdrop',
            'upstream',
            'myvidplay.com',
            'vidplay',
        ]
        
        print(f"\n{'='*60}")
        print(f"🎬 Processing movie: {movie.title}")
        print(f"{'='*60}")
        
        for link in data.get('links', []):
            stream_url = link.get('stream_url', '').lower()
            server_name = link.get('server_name', '').lower()
            
            # Check if URL contains any problematic domain
            needs_proxy = any(domain in stream_url for domain in PROXY_DOMAINS)
            
            # Get the actual StreamingLink ID for proxy URL
            try:
                streaming_link = StreamingLink.objects.filter(
                    movie=movie, 
                    stream_url=link['stream_url']
                ).first()
                link['link_id'] = streaming_link.id if streaming_link else None
            except:
                link['link_id'] = None
            
            link['needs_proxy'] = needs_proxy
            
            # Debug logging
            print(f"\n📺 Server: {link.get('server_name')}")
            print(f"   URL: {link.get('stream_url')[:60]}...")
            print(f"   Link ID: {link['link_id']}")
            print(f"   🔒 Needs Proxy: {needs_proxy}")
            
            if needs_proxy and link['link_id']:
                proxy_url = f"/player/{imdb_id}/{link['link_id']}/"
                print(f"   ✅ Proxy URL: {proxy_url}")
            else:
                print(f"   ⚠️  Direct embed (may fail)")
        
        print(f"{'='*60}\n")
        
        return Response(data)


def player_proxy(request, imdb_id, link_id):
    """
    Enhanced proxy that fetches embed page content and extracts video player
    This bypasses X-Frame-Options by not using iframes at all
    """
    try:
        movie = Movie.objects.get(imdb_id=imdb_id)
        link = StreamingLink.objects.filter(id=link_id, is_active=True).first()
        
        if not link:
            return HttpResponse("Link not found or inactive", status=404)
        
        # Fetch the embed page content
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://goojara.to/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(link.stream_url, headers=headers, timeout=15)
            embed_html = response.text
            
            # Extract the base URL for relative paths
            from urllib.parse import urlparse
            parsed_url = urlparse(link.stream_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Inject our custom HTML wrapper that fixes relative URLs
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="referrer" content="no-referrer">
    <title>{movie.title} - {link.server_name}</title>
    <base href="{base_url}/">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body, html {{
            width: 100%;
            height: 100vh;
            overflow: hidden;
            background: #000;
        }}
        .server-info {{
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.9);
            padding: 8px 15px;
            border-radius: 6px;
            color: #4CAF50;
            font-size: 12px;
            z-index: 9999;
            font-family: Arial, sans-serif;
        }}
        /* Hide ads and popups */
        .ad, .ads, [class*="ad-"], [id*="ad-"],
        [class*="popup"], [id*="popup"] {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="server-info">
        🔒 Proxy Mode • {link.server_name} • {link.quality}
    </div>
    
    <!-- Injected embed content -->
    <div id="embed-container">
        {embed_html}
    </div>
    
    <script>
        // Block popup attempts
        window.open = function() {{ return null; }};
        
        // Remove any ad elements that load dynamically
        setInterval(function() {{
            const ads = document.querySelectorAll('.ad, .ads, [class*="ad-"], [id*="ad-"], [class*="popup"], [id*="popup"]');
            ads.forEach(ad => ad.remove());
        }}, 1000);
        
        console.log('Proxy player loaded successfully');
    </script>
</body>
</html>
            """
            
            django_response = HttpResponse(html)
            django_response['X-Frame-Options'] = 'SAMEORIGIN'
            django_response['Content-Security-Policy'] = "frame-ancestors 'self'"
            return django_response
            
        except requests.RequestException as e:
            # If fetching fails, return error page
            error_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error Loading Player</title>
    <style>
        body {{
            background: #121212;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }}
        .error-box {{
            background: #1e1e1e;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            max-width: 500px;
        }}
        .error-box h2 {{
            color: #e50914;
            margin-bottom: 20px;
        }}
        .error-box p {{
            color: #ccc;
            margin: 10px 0;
        }}
        .btn {{
            margin-top: 20px;
            padding: 12px 30px;
            background: #e50914;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{
            background: #f40612;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <h2>⚠️ Unable to Load Video</h2>
        <p>Server: {link.server_name}</p>
        <p>The video server is not responding.</p>
        <p style="font-size: 0.9em; color: #888;">Error: {str(e)[:100]}</p>
        <a href="javascript:location.reload()" class="btn">🔄 Retry</a>
        <a href="javascript:window.close()" class="btn" style="background: #666;">✖ Close</a>
    </div>
</body>
</html>
            """
            return HttpResponse(error_html, status=500)
        
    except Movie.DoesNotExist:
        return HttpResponse("Movie not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@require_http_methods(["GET"])
def extract_video_url(request):
    """Extract actual video URL from embed services"""
    embed_url = request.GET.get('url')
    
    if not embed_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://sflix.ps/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(embed_url, headers=headers, timeout=10)
        html = response.text
        
        # Method 1: M3U8 URLs
        m3u8_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
        m3u8_matches = re.findall(m3u8_pattern, html)
        
        if m3u8_matches:
            return JsonResponse({
                'success': True,
                'video_url': m3u8_matches[0],
                'type': 'm3u8',
                'message': 'Found HLS stream'
            })
        
        # Method 2: MP4 URLs
        mp4_pattern = r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)'
        mp4_matches = re.findall(mp4_pattern, html)
        
        if mp4_matches:
            return JsonResponse({
                'success': True,
                'video_url': mp4_matches[0],
                'type': 'mp4',
                'message': 'Found MP4 stream'
            })
        
        # Method 3: Video player configs
        video_patterns = [
            r'"file"\s*:\s*"([^"]+)"',
            r'"src"\s*:\s*"([^"]+)"',
            r'"url"\s*:\s*"([^"]+)"',
            r'source\s*:\s*"([^"]+)"',
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
        
        # Fallback
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
    """Proxy video streams to avoid CORS"""
    video_url = request.GET.get('url')
    
    if not video_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://sflix.ps/',
            'Origin': 'https://sflix.ps',
        }
        
        response = requests.get(video_url, headers=headers, stream=True, timeout=10)
        
        django_response = HttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('content-type', 'video/mp4')
        )
        
        for header in ['Content-Length', 'Accept-Ranges', 'Content-Range']:
            if header in response.headers:
                django_response[header] = response.headers[header]
        
        return django_response
        
    except Exception as e:
        return HttpResponse(f'Error proxying video: {str(e)}', status=500)