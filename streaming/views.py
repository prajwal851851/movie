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
from django.views.decorators.clickjacking import xframe_options_exempt
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
            # NOTE: sysmeasuring removed - URLs in DB are incomplete (just domain, no path)
            # Need to re-scrape to get full embed URLs
        ]
        
        print(f"\n{'='*60}")
        print(f"Processing movie: {movie.title}")
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



@xframe_options_exempt
@require_http_methods(["GET"])
def player_proxy(request, imdb_id, link_id):
    """
    Enhanced proxy that fetches embed page content and bypasses sandbox/CORS restrictions
    Removes sandbox detection scripts and adds anti-detection measures
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
            
            # SELECTIVE SCRIPT REMOVAL - Remove ONLY obvious ad scripts
            import re
            
            cleaned_html = embed_html
            
            # Step 1: Remove ONLY external scripts from known ad domains
            ad_domains = [
                'doubleclick', 'googlesyndication', 'adservice', 'adsense',
                'topworkredbay', 'popads', 'popcash', 'adnxs', 'advertising',
                'taboola', 'outbrain', 'criteo', 'pubmatic', 'openx'
            ]
            
            # Find all script tags with src
            external_scripts = re.findall(r'<script[^>]*src=["\'][^"\']*["\'][^>]*>.*?</script>', cleaned_html, re.IGNORECASE | re.DOTALL)
            for script in external_scripts:
                # Check if it's from an ad domain
                script_lower = script.lower()
                if any(ad_domain in script_lower for ad_domain in ad_domains):
                    cleaned_html = cleaned_html.replace(script, '')
                    
            # Step 2: Remove ONLY inline scripts that explicitly call window.open or do redirects
            # Be very specific to avoid breaking video player scripts
            inline_scripts = re.findall(r'<script(?![^>]*src)[^>]*>.*?</script>', cleaned_html, re.IGNORECASE | re.DOTALL)
            for script in inline_scripts:
                script_content = script.lower()
                # Only remove if it has BOTH popup/redirect AND is very short (likely just an ad trigger)
                has_popup = 'window.open(' in script_content or 'window.open (' in script_content
                has_redirect = 'location.href=' in script_content or 'location.replace(' in script_content
                is_short = len(script) < 500  # Short scripts are likely just ad triggers
                
                if (has_popup or has_redirect) and is_short:
                    cleaned_html = cleaned_html.replace(script, '')
            
            # Step 3: Remove ad iframes (but keep video iframes)
            cleaned_html = re.sub(
                r'<iframe[^>]*src=["\'][^"\']*(?:doubleclick|googlesyndication|adservice|popads)[^"\']*["\'][^>]*>.*?</iframe>',
                '',
                cleaned_html,
                flags=re.IGNORECASE | re.DOTALL
            )
            
            # Step 4: Remove meta refresh tags (used for redirects)
            cleaned_html = re.sub(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*>', '', cleaned_html, flags=re.IGNORECASE)
            
            # Inject our custom HTML wrapper with anti-detection code
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
        /* AGGRESSIVE AD BLOCKING - Hide ads, popups, banners, and overlays */
        .ad, .ads, [class*="ad-"], [id*="ad-"],
        [class*="popup"], [id*="popup"],
        [class*="banner"], [id*="banner"],
        [class*="overlay"], [id*="overlay"],
        [class*="sponsor"], [id*="sponsor"],
        [class*="advertisement"], [id*="advertisement"] {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        
        /* Hide common ad container patterns */
        div[id^="ad"], div[class^="ad"],
        div[id*="banner"], div[class*="banner"],
        div[id*="popup"], div[class*="popup"] {{
            display: none !important;
        }}
        
        /* Prevent click-through overlays */
        div[style*="position: absolute"][style*="z-index"] {{
            pointer-events: none !important;
        }}
    </style>
    
    <script>
        // IMMEDIATE POPUP BLOCKING - Run FIRST before ANY other scripts
        (function() {{
            'use strict';
            
            // Block window.open IMMEDIATELY
            const noop = function() {{ 
                console.log('🚫 IMMEDIATE: Blocked window.open'); 
                return null; 
            }};
            
            window.open = noop;
            window.showModalDialog = noop;
            
            // Prevent window.open from being redefined
            Object.defineProperty(window, 'open', {{
                value: noop,
                writable: false,
                configurable: false
            }});
            
            // Block ALL event listeners that might open popups
            const originalAddEventListener = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(type, listener, options) {{
                // If it's a click/mousedown event, wrap it to block popups
                if (type === 'click' || type === 'mousedown' || type === 'mouseup' || type === 'touchstart') {{
                    const wrappedListener = function(event) {{
                        // Temporarily override window.open during this event
                        const tempOpen = window.open;
                        window.open = noop;
                        
                        try {{
                            return listener.apply(this, arguments);
                        }} finally {{
                            window.open = noop; // Keep it blocked
                        }}
                    }};
                    return originalAddEventListener.call(this, type, wrappedListener, options);
                }}
                return originalAddEventListener.call(this, type, listener, options);
            }};
            
            console.log('🛡️ IMMEDIATE popup blocking active');
        }})();
    </script>
    
    <script>
        // NUCLEAR AD BLOCKING - Execute BEFORE any other scripts
        (function() {{
            'use strict';
            
            console.log('🚀 Initializing nuclear ad-blocking...');
            
            
            // ============================================
            // PART 1: ULTRA-AGGRESSIVE CLICK BLOCKING
            // ============================================
            
            // Block ALL clicks by default, only allow specific video controls
            function blockAllClicksExceptVideo(e) {{
                const target = e.target;
                const tagName = target.tagName;
                
                // ONLY allow clicks on these specific elements
                const allowedElements = [
                    'VIDEO',           // The actual video element
                    'BUTTON',          // Player control buttons
                    'INPUT'            // Volume sliders, etc.
                ];
                
                // Check if it's an allowed element
                if (allowedElements.includes(tagName)) {{
                    console.log('✅ Allowed click on:', tagName);
                    return true;
                }}
                
                // Check if it's a video control by class
                const className = target.className || '';
                const id = target.id || '';
                
                const isVideoControl = 
                    className.includes('vjs-') ||      // Video.js controls
                    className.includes('jw-') ||       // JW Player controls
                    className.includes('plyr__') ||    // Plyr controls
                    className.includes('dplayer-') ||  // DPlayer controls
                    id.includes('control') ||
                    id.includes('play') ||
                    id.includes('pause') ||
                    id.includes('volume');
                
                if (isVideoControl) {{
                    console.log('✅ Allowed click on video control');
                    return true;
                }}
                
                // BLOCK EVERYTHING ELSE
                e.stopPropagation();
                e.stopImmediatePropagation();
                e.preventDefault();
                console.log('🚫 BLOCKED click on:', tagName, className.substring(0, 30));
                return false;
            }}
            
            // Capture ALL click/mouse events at document level (useCapture = true runs FIRST)
            document.addEventListener('click', blockAllClicksExceptVideo, true);
            document.addEventListener('mousedown', blockAllClicksExceptVideo, true);
            document.addEventListener('mouseup', blockAllClicksExceptVideo, true);
            document.addEventListener('touchstart', blockAllClicksExceptVideo, true);
            document.addEventListener('touchend', blockAllClicksExceptVideo, true);
            
            // Also block auxclick (middle/right click)
            document.addEventListener('auxclick', function(e) {{
                e.stopPropagation();
                e.stopImmediatePropagation();
                e.preventDefault();
                console.log('🚫 BLOCKED auxclick');
                return false;
            }}, true);
            
            // ============================================
            // PART 2: SMART NAVIGATION LOCKDOWN
            // ============================================
            
            // Override location methods without freezing (to avoid TypeError)
            const originalReplace = window.location.replace;
            const originalAssign = window.location.assign;
            const originalReload = window.location.reload;
            
            // Block location.replace (used for redirects)
            try {{
                window.location.replace = function(url) {{
                    // Allow same-origin navigation
                    if (url && url.includes(window.location.hostname)) {{
                        return originalReplace.call(window.location, url);
                    }}
                    console.log('🚫 Blocked location.replace to:', url);
                    return false;
                }};
            }} catch(e) {{}}
            
            // Block location.assign
            try {{
                window.location.assign = function(url) {{
                    if (url && url.includes(window.location.hostname)) {{
                        return originalAssign.call(window.location, url);
                    }}
                    console.log('🚫 Blocked location.assign to:', url);
                    return false;
                }};
            }} catch(e) {{}}
            
            // Monitor location.href changes
            let currentHref = window.location.href;
            setInterval(function() {{
                if (window.location.href !== currentHref) {{
                    console.log('🚫 Detected location.href change, reverting');
                    window.location.href = currentHref;
                }}
            }}, 100);
            
            // Block history API
            window.history.pushState = function() {{
                console.log('🚫 Blocked history.pushState');
                return false;
            }};
            window.history.replaceState = function() {{
                console.log('🚫 Blocked history.replaceState');
                return false;
            }};
            
            // ============================================
            // PART 3: POPUP BLOCKING
            // ============================================
            
            window.open = function() {{ 
                console.log('🚫 Blocked window.open popup'); 
                return null; 
            }};
            
            window.showModalDialog = function() {{
                console.log('🚫 Blocked showModalDialog');
                return null;
            }};
            
            // ============================================
            // PART 4: ANTI-DETECTION
            // ============================================
            
            // Override document.domain to prevent sandbox detection
            try {{
                Object.defineProperty(document, 'domain', {{
                    get: function() {{ return '{parsed_url.netloc}'; }},
                    set: function() {{ return true; }}
                }});
            }} catch(e) {{}}
            
            // Disable iframe detection
            window.self = window.top;
            window.parent = window.top;
            
            // Disable adblock detection
            Object.defineProperty(window, 'adblock', {{
                get: function() {{ return false; }},
                set: function() {{ return false; }}
            }});
            
            console.log('✅ Nuclear ad-blocking initialized');
        }})();
    </script>
</head>
<body>
    <div class="server-info">
        🔒 Proxy Mode • {link.server_name} • {link.quality}
    </div>
    
    <!-- Injected embed content -->
    <div id="embed-container">
        {cleaned_html}
    </div>
    
    <script>
        // NUCLEAR RUNTIME PROTECTION - Continuous monitoring and removal
        (function() {{
            'use strict';
            
            console.log('🛡️ Starting runtime protection...');
            
            // ============================================
            // AGGRESSIVE IFRAME REMOVAL
            // ============================================
            
            // Remove ALL iframes except video players (check every 200ms)
            setInterval(function() {{
                const iframes = document.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    const src = (iframe.src || '').toLowerCase();
                    const id = (iframe.id || '').toLowerCase();
                    const className = (iframe.className || '').toLowerCase();
                    
                    // Keep if it's clearly a video player
                    const isVideoPlayer = 
                        src.includes('player') ||
                        src.includes('embed') ||
                        src.includes('video') ||
                        src.includes('/e/') ||  // Common video embed path
                        src.includes('/v/') ||  // Common video embed path
                        id.includes('player') ||
                        id.includes('video') ||
                        className.includes('player') ||
                        className.includes('video');
                    
                    // Remove ONLY if it's clearly an ad
                    const isAd = 
                        src.includes('ad') || 
                        src.includes('popup') || 
                        src.includes('banner') ||
                        src.includes('doubleclick') ||
                        src.includes('googlesyndication') ||
                        src.includes('adservice') ||
                        src.includes('popads');
                    
                    if (isAd && !isVideoPlayer) {{
                        iframe.remove();
                        console.log('🗑️ Removed ad iframe:', src.substring(0, 50));
                    }}
                }});
            }}, 200); // Check every 200ms
            
            // ============================================
            // AGGRESSIVE AD ELEMENT REMOVAL
            // ============================================
            
            setInterval(function() {{
                // Remove ALL anchor tags (ads use <a> tags for clickable overlays)
                const links = document.querySelectorAll('a');
                links.forEach(link => {{
                    // Keep ONLY if it's clearly not an ad
                    const href = (link.href || '').toLowerCase();
                    const isInternal = href.includes(window.location.hostname) || href === '';
                    
                    // Remove ALL external links (they're all ads)
                    if (!isInternal) {{
                        link.remove();
                        console.log('🗑️ Removed ad link');
                    }}
                }});
                
                // Remove ad elements by class/id
                const ads = document.querySelectorAll(
                    '.ad, .ads, [class*="ad-"], [id*="ad-"], ' +
                    '[class*="popup"], [id*="popup"], ' +
                    '[class*="banner"], [id*="banner"], ' +
                    '[class*="overlay"], [id*="overlay"]'
                );
                ads.forEach(ad => {{
                    // Only remove if it's not the video player
                    if (!ad.querySelector('video') && !ad.closest('video')) {{
                        ad.remove();
                    }}
                }});
                
                // Remove ALL divs with position:absolute that cover the whole screen (ad overlays)
                const allDivs = document.querySelectorAll('div');
                allDivs.forEach(div => {{
                    const style = window.getComputedStyle(div);
                    const position = style.position;
                    const zIndex = parseInt(style.zIndex) || 0;
                    const width = parseInt(style.width) || 0;
                    const height = parseInt(style.height) || 0;
                    
                    // Remove if it's a full-screen overlay with high z-index (likely an ad)
                    if (position === 'absolute' && zIndex > 100 && width > 300 && height > 300) {{
                        // Don't remove if it contains video
                        if (!div.querySelector('video')) {{
                            div.remove();
                            console.log('🗑️ Removed overlay div');
                        }}
                    }}
                }});
            }}, 100); // Check every 100ms for aggressive removal
            
            // ============================================
            // MUTATION OBSERVER - Block injected scripts
            // ============================================
            
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    mutation.addedNodes.forEach(function(node) {{
                        // Block injected scripts
                        if (node.tagName === 'SCRIPT') {{
                            const src = (node.src || '').toLowerCase();
                            const content = (node.textContent || '').toLowerCase();
                            
                            // Block if it's an ad script
                            if (src.includes('ad') || src.includes('popup') || 
                                src.includes('topworkredbay') || src.includes('popads') ||
                                content.includes('window.open') || content.includes('popup') ||
                                content.includes('location.href') || content.includes('redirect')) {{
                                node.remove();
                                console.log('🚫 Blocked injected script');
                            }}
                        }}
                        
                        // Block injected iframes
                        if (node.tagName === 'IFRAME') {{
                            const src = (node.src || '').toLowerCase();
                            if (!src.includes('player') && !src.includes('video')) {{
                                node.remove();
                                console.log('🚫 Blocked injected iframe');
                            }}
                        }}
                    }});
                }});
            }});
            
            observer.observe(document.documentElement, {{
                childList: true,
                subtree: true
            }});
            
            // ============================================
            // RE-ENFORCE PROTECTIONS
            // ============================================
            
            // Re-block window.open every second (in case it's overridden)
            setInterval(function() {{
                window.open = function() {{ 
                    console.log('🚫 Blocked late popup attempt'); 
                    return null; 
                }};
                
                // Re-enforce iframe/sandbox detection blocks
                window.self = window.top;
                window.parent = window.top;
            }}, 1000);
            
            console.log('✅ Runtime protection active');
        }})();
    </script>
</body>
</html>
            """
            
            # Create response with balanced security headers
            django_response = HttpResponse(html)
            
            # Balanced Content Security Policy - Allow video resources but block ads
            django_response['Content-Security-Policy'] = (
                "default-src 'self' https:; "  # Allow HTTPS by default
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "  # Allow scripts for player
                "style-src 'self' 'unsafe-inline' https:; "  # Allow external stylesheets
                "img-src 'self' data: https: http: blob:; "  # Allow images
                "media-src 'self' https: http: blob: data:; "  # Allow video from any source
                "connect-src 'self' https: http:; "  # Allow connections
                "font-src 'self' https: data:; "  # Allow fonts
                "frame-src 'self' https: http:; "  # Allow iframes for video (our JS will filter ads)
                "object-src 'none'; "  # Block plugins
                "base-uri *; "  # Allow base tag (needed for relative URLs)
            )
            
            # CORS bypass headers
            django_response['Access-Control-Allow-Origin'] = '*'
            django_response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            django_response['Access-Control-Allow-Headers'] = '*'
            
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