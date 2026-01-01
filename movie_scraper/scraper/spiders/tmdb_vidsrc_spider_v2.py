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


class TmdbVidsrcSpiderV2(scrapy.Spider):
    name = 'tmdb_vidsrc_v2'
    
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
        """Fetch MOVIES ONLY using Yearly Discovery to bypass TMDB limits"""
        self.logger.info('🚀 Starting TMDB-VidSrc Spider V2 (DEEP SCRAPE MODE)')
        self.logger.info(f'📊 Target: {self.limit} items per session')
        
        # Iterate through years to bypass the 500-page limit (10k items)
        import datetime
        # Create a list of years and shuffle it for randomness
        import random
        current_year = datetime.datetime.now().year
        years = list(range(2002, current_year + 1))
        random.shuffle(years)
        
        discovery_pool = []
        
        for year in years:
            # Randomize sorting for this year
            sort_options = ['popularity.desc', 'vote_average.desc', 'revenue.desc', 'primary_release_date.desc']
            selected_sort = random.choice(sort_options)
            
            # Fetch pages for each year
            pages_to_fetch = min(40, self.max_pages) # Reduced per year to increase "spread"
            for page in range(1, pages_to_fetch + 1):
                discovery_pool.append({
                    'year': year,
                    'page': page,
                    'sort': selected_sort
                })

        # Shuffle the entire pool for total randomness
        random.shuffle(discovery_pool)
        
        self.logger.info(f'🎲 Hyper-Discovery Mode: Interleaving {len(discovery_pool)} movie requests across all years')
        
        for task in discovery_pool:
            if self.count >= self.limit:
                break
                
            url = (
                f'https://api.themoviedb.org/3/discover/movie?'
                f'api_key={self.api_key}&'
                f'primary_release_year={task["year"]}&'
                f'include_adult=true&'
                f'page={task["page"]}&'
                f'sort_by={task["sort"]}'
            )
            yield scrapy.Request(
                url, 
                callback=self.parse_popular_movies,
                meta={'page': task['page'], 'year': task['year']}
            )
    
    def parse_popular_movies(self, response):
        """Parse discovered movies list for a specific year"""
        page = response.meta.get('page')
        year = response.meta.get('year')
        try:
            data = json.loads(response.text)
            movies = data.get('results', [])
            
            if not movies:
                return # No more movies for this year

            self.logger.info(f'📅 {year} | Page {page}: Found {len(movies)} items')
            
            for movie in movies:
                if self.count >= self.limit: return
                
                movie_id = movie.get('id')
                if not movie_id: continue
                
                detail_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.api_key}&append_to_response=external_ids,credits,keywords'
                yield scrapy.Request(detail_url, callback=self.parse_movie_detail, meta={'tmdb_id': movie_id})
        except Exception as e:
            self.logger.error(f'❌ Error parsing movies for {year} Page {page}: {e}')

    def parse_movie_detail(self, response):
        """Parse individual movie details with extended metadata"""
        try:
            data = json.loads(response.text)
            imdb_id = data.get('external_ids', {}).get('imdb_id')
            
            if not imdb_id:
                return

            # Determine Status
            tmdb_status = data.get('status', 'Unknown')
            year_val = None
            if data.get('release_date'):
                try:
                    year_val = int(data['release_date'][:4])
                except:
                    pass
            
            # Logic: If NOT Released OR Year > CURRENT_YEAR, it's Upcoming
            import datetime
            current_year = datetime.datetime.now().year
            
            if tmdb_status != 'Released' or (year_val and year_val > current_year):
                status = 'Upcoming'
            else:
                status = 'Released'

            vidsrc_to_url = f'https://vidsrc.to/embed/movie/{imdb_id}'
            vidsrc_me_url = f'https://vidsrc.me/embed/movie?imdb={imdb_id}'
            
            year = None
            if data.get('release_date'):
                try: year = int(data['release_date'][:4])
                except: pass
            
            # Extract Crew
            directors = [p['name'] for p in data.get('credits', {}).get('crew', []) if p.get('job') == 'Director']
            writers = [p['name'] for p in data.get('credits', {}).get('crew', []) if p.get('job') in ['Writer', 'Screenplay', 'Author']]
            
            # Extract Keywords
            keywords = [k['name'] for k in data.get('keywords', {}).get('keywords', [])]
            
            # Extract Genres
            genres = [g['name'] for g in data.get('genres', [])]

            item = MovieItem()
            item['imdb_id'] = imdb_id
            item['title'] = data.get('title', 'Unknown')
            item['year'] = year
            item['synopsis'] = data.get('overview', '')
            item['poster_url'] = f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get('poster_path') else ''
            item['source_site'] = 'tmdb_vidsrc'
            item['source_url'] = f"https://www.themoviedb.org/movie/{data['id']}"
            item['quality'] = 'HD'
            item['language'] = 'EN'
            item['content_type'] = 'movie'
            
            # Extended Metadata
            item['metadata'] = {
                'genres': genres,
                'user_score': data.get('vote_average'),
                'directors': directors,
                'writers': writers,
                'original_title': data.get('original_title'),
                'status': status,
                'original_language': data.get('original_language'),
                'budget': data.get('budget'),
                'revenue': data.get('revenue'),
                'keywords': keywords
            }

            # Instead of yielding immediately, we validate the link first
            self.logger.info(f'🔍 Validating link for [MOVIE] {item["title"]} ({year})...')
            
            yield scrapy.Request(
                vidsrc_to_url,
                callback=self.validate_movie_link,
                meta={
                    'item': item,
                    'vidsrc_to_url': vidsrc_to_url,
                    'vidsrc_me_url': vidsrc_me_url,
                    'year': year,
                    'status': status
                },
                priority=10 # Higher priority for validation requests
            )
            
        except Exception as e:
            self.logger.error(f'❌ Error processing movie: {e}')

    def validate_movie_link(self, response):
        """Check if the provider actually has the movie content"""
        item = response.meta['item']
        vidsrc_to_url = response.meta['vidsrc_to_url']
        vidsrc_me_url = response.meta['vidsrc_me_url']
        year = response.meta['year']
        status = response.meta['status']
        
        html_content = response.text.lower()
        
        # Markers that indicate the media is unavailable
        unavailable_markers = [
            "media is unavailable",
            "this video is not available",
            "video not found",
            "no link found",
            "at the moment", # From "This media is unavailable at the moment"
            "unavailable"
        ]
        
        if any(marker in html_content for marker in unavailable_markers) or response.status != 200:
            self.logger.warning(f'⏭️ Skipping [MOVIE] {item["title"]} ({year}) - Media unavailable on provider')
            return

        # If we reached here, the link is likely valid
        self.count += 1
        self.stats['successful'] += 1
        log_icon = '📅' if status == 'Upcoming' else '✓'
        self.logger.info(f'{log_icon} [MOVIE] {item["title"]} ({year}) - Link Validated!')

        # Yield link 1: VidSrc To
        item_to = item.copy()
        item_to['stream_url'] = vidsrc_to_url
        item_to['server_name'] = 'VidSrc To'
        yield item_to

        # Yield link 2: VidSrc Me
        item_me = item.copy()
        item_me['stream_url'] = vidsrc_me_url
        item_me['server_name'] = 'VidSrc Me'
        yield item_me
            



