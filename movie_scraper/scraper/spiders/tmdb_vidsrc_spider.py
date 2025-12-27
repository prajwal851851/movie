# scraper/spiders/tmdb_vidsrc_spider.py
"""
TMDB-VidSrc Spider
Fetches popular movies from TMDB API and generates VidSrc embed links
No scraping needed - uses clean REST API
"""
import scrapy
from scrapy import signals
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from scraper.items import MovieItem
from streaming.models import Movie


class TmdbVidsrcSpider(scrapy.Spider):
    name = 'tmdb_vidsrc'
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 5,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, api_key=None, limit=100, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not api_key:
            raise ValueError('TMDB API key is required. Use --api-key parameter')
        
        self.api_key = api_key
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.count = 0
        self.existing_imdb_ids = set()
        
        # Statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'skipped_no_imdb': 0,
            'skipped_existing': 0,
            'errors': 0
        }
        
        self._load_existing_movies()
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    
    def spider_closed(self, spider):
        """Show final statistics"""
        self.logger.info('\n' + '='*70)
        self.logger.info('🎬 TMDB-VIDSRC SPIDER SUMMARY')
        self.logger.info('='*70)
        self.logger.info(f'Movies Attempted:     {self.stats["attempted"]}')
        self.logger.info(f'✓ Successful:         {self.stats["successful"]}')
        self.logger.info(f'⊘ No IMDb ID:         {self.stats["skipped_no_imdb"]}')
        self.logger.info(f'⊘ Already Exists:     {self.stats["skipped_existing"]}')
        if self.stats['errors'] > 0:
            self.logger.info(f'❌ Errors:            {self.stats["errors"]}')
        self.logger.info('='*70 + '\n')
    
    def _load_existing_movies(self):
        """Load existing IMDb IDs to avoid duplicates"""
        try:
            movies = Movie.objects.filter(imdb_id__startswith='tt').values_list('imdb_id', flat=True)
            self.existing_imdb_ids = set(movies)
            self.logger.info(f'📚 Loaded {len(self.existing_imdb_ids)} existing movies with IMDb IDs')
        except Exception as e:
            self.logger.warning(f'⚠️  Could not load existing movies: {e}')
    
    def start_requests(self):
        """Fetch popular movies from TMDB"""
        self.logger.info('🚀 Starting TMDB-VidSrc Spider')
        self.logger.info(f'📊 Target: {self.limit} movies from {self.max_pages} pages')
        
        for page in range(1, self.max_pages + 1):
            if self.count >= self.limit:
                break
            
            url = f'https://api.themoviedb.org/3/movie/popular?api_key={self.api_key}&page={page}'
            yield scrapy.Request(url, callback=self.parse_popular, meta={'page': page})
    
    def parse_popular(self, response):
        """Parse popular movies list"""
        page = response.meta['page']
        
        try:
            data = json.loads(response.text)
            movies = data.get('results', [])
            
            self.logger.info(f'📄 Page {page}: Found {len(movies)} movies')
            
            for movie in movies:
                if self.count >= self.limit:
                    return
                
                movie_id = movie.get('id')
                if not movie_id:
                    continue
                
                # Fetch detailed movie info including IMDb ID
                detail_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.api_key}&append_to_response=external_ids'
                yield scrapy.Request(
                    detail_url,
                    callback=self.parse_movie,
                    meta={'tmdb_id': movie_id}
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f'❌ Failed to parse JSON from page {page}: {e}')
            self.stats['errors'] += 1
    
    def parse_movie(self, response):
        """Parse individual movie details"""
        self.stats['attempted'] += 1
        
        try:
            data = json.loads(response.text)
            
            # Get IMDb ID
            imdb_id = data.get('external_ids', {}).get('imdb_id')
            
            if not imdb_id:
                self.logger.warning(f'⚠️  No IMDb ID for: {data.get("title")}')
                self.stats['skipped_no_imdb'] += 1
                return
            
            # Check if already exists
            if imdb_id in self.existing_imdb_ids:
                self.stats['skipped_existing'] += 1
                return
            
            # Generate VidSrc URL
            vidsrc_url = f'https://vidsrc.to/embed/movie/{imdb_id}'
            
            # Extract year from release_date
            year = None
            if data.get('release_date'):
                try:
                    year = int(data['release_date'][:4])
                except (ValueError, IndexError):
                    pass
            
            # Build poster URL
            poster_url = ''
            if data.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
            
            # Create movie item
            item = MovieItem()
            item['imdb_id'] = imdb_id
            item['title'] = data.get('title', 'Unknown')
            item['year'] = year
            item['synopsis'] = data.get('overview', '')
            item['poster_url'] = poster_url
            item['source_site'] = 'tmdb_vidsrc'
            item['source_url'] = f"https://www.themoviedb.org/movie/{data['id']}"
            item['stream_url'] = vidsrc_url
            item['server_name'] = 'VidSrc'
            item['quality'] = 'HD'
            item['language'] = 'EN'
            
            self.count += 1
            self.stats['successful'] += 1
            
            self.logger.info(
                f'✓ [{self.count}/{self.limit}] {item["title"]} ({year})\n'
                f'   IMDb: {imdb_id}\n'
                f'   VidSrc: {vidsrc_url}'
            )
            
            yield item
            
        except json.JSONDecodeError as e:
            self.logger.error(f'❌ Failed to parse movie JSON: {e}')
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f'❌ Error processing movie: {e}')
            self.stats['errors'] += 1
