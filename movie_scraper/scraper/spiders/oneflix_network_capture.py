# scraper/spiders/oneflix_network_capture.py
"""
Advanced 1Flix Spider with Network Request Capture
Uses Chrome DevTools Protocol to intercept network requests and capture complete video URLs
"""
import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from scraper.items import MovieItem
import time
import re
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie

class OneflixNetworkCaptureSpider(scrapy.Spider):
    name = 'oneflix_network'
    allowed_domains = ['1flix.to']
    start_urls = [
        'https://1flix.to/top-imdb',
        'https://1flix.to/movie',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, limit=50, max_pages=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.count = 0
        self.seen_urls = set()
        self.pages_scraped = {}
        self.existing_movie_urls = set()
        self.network_requests = []
        
        # Statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'network_captured': 0
        }
        
        self._load_existing_movies()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium with network logging enabled"""
        self.logger.info('🚀 Initializing Network Capture Spider...')
        
        # Enable performance logging to capture network requests
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable performance logging
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info('✓ Selenium with Network Logging initialized')
        except Exception as e:
            self.logger.error(f'❌ Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        """Cleanup and show statistics"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        
        self.logger.info('\\n' + '='*70)
        self.logger.info('🎬 SCRAPING SUMMARY - NETWORK CAPTURE SPIDER')
        self.logger.info('='*70)
        self.logger.info(f'Movies Attempted:    {self.stats["attempted"]}')
        self.logger.info(f'✓ Successful:        {self.stats["successful"]}')
        self.logger.info(f'✗ Failed:            {self.stats["failed"]}')
        self.logger.info(f'📡 Network Captured: {self.stats["network_captured"]}')
        self.logger.info('='*70 + '\\n')

    def _load_existing_movies(self):
        """Load existing movies to avoid duplicates"""
        try:
            movies = Movie.objects.all().values_list('source_url', flat=True)
            self.existing_movie_urls = set(url for url in movies if url)
            self.logger.info(f'📚 Loaded {len(self.existing_movie_urls)} existing movies')
        except Exception as e:
            self.logger.warning(f'⚠️  Could not load existing movies: {e}')

    def get_network_requests(self):
        """Extract network requests from browser logs"""
        logs = self.driver.get_log('performance')
        requests = []
        
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                
                # Look for network requests
                if log['method'] == 'Network.requestWillBeSent':
                    url = log['params']['request']['url']
                    # Filter for video embed URLs
                    if any(domain in url for domain in ['videostr.net', 'megacloud', 'vidcloud', 'embed']):
                        if '/e-1/' in url or '/embed' in url:
                            requests.append(url)
                            
            except Exception:
                continue
        
        return requests

    def parse(self, response):
        """Parse movie listing pages"""
        self.logger.info(f'📄 Loading page: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(4)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            all_links = sel_response.css('a::attr(href)').getall()
            
            movies_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    break
                
                if link and re.match(r'^/movie/watch-[\\w-]+-\\d+', link):
                    full_url = response.urljoin(link)
                    
                    if full_url in self.seen_urls or full_url in self.existing_movie_urls:
                        continue
                    
                    self.seen_urls.add(full_url)
                    movies_found += 1
                    self.count += 1
                    
                    yield scrapy.Request(url=full_url, callback=self.parse_movie, dont_filter=True)
            
            self.logger.info(f'✓ Queued {movies_found} movies (Total: {self.count}/{self.limit})')
            
            # Pagination
            if movies_found > 0 and self.count < self.limit:
                base_url = response.url.split('?')[0]
                current_page = self.pages_scraped.get(base_url, 1)
                
                if current_page < self.max_pages:
                    next_page = current_page + 1
                    next_url = f"{base_url}?page={next_page}"
                    self.pages_scraped[base_url] = next_page
                    yield scrapy.Request(url=next_url, callback=self.parse, dont_filter=True)
            
        except Exception as e:
            self.logger.error(f'❌ Error parsing page: {e}')

    def parse_movie(self, response):
        """Parse individual movie with network capture"""
        self.stats['attempted'] += 1
        
        try:
            self.driver.get(response.url)
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            # Extract movie metadata
            item = MovieItem()
            item['source_site'] = '1flix.to'
            item['source_url'] = response.url
            
            movie_id_match = re.search(r'-(\\d+)$', response.url)
            movie_id = movie_id_match.group(1) if movie_id_match else response.url.split('/')[-1]
            item['imdb_id'] = f'1flix_{movie_id}'
            
            # Title and year
            title_elem = sel_response.css('h2.heading-name a::text, .film-name::text').get()
            if not title_elem:
                self.logger.warning(f'⚠️  No title found, skipping: {response.url}')
                self.stats['failed'] += 1
                return
            
            title_text = re.sub(r'^Watch\\s+', '', title_elem.strip(), flags=re.IGNORECASE)
            title_text = re.sub(r'\\s+Online\\s+free$', '', title_text, flags=re.IGNORECASE)
            
            title_match = re.search(r'(.+?)\\s+(\\d{4})', title_text)
            if title_match:
                item['title'] = title_match.group(1).strip()
                item['year'] = int(title_match.group(2))
            else:
                item['title'] = title_text
                item['year'] = None
            
            self.logger.info(f'\\n🎬 Processing: {item["title"]} ({item["year"]})')
            
            # Synopsis and poster
            synopsis = sel_response.css('.description::text').get()
            item['synopsis'] = synopsis.strip() if synopsis else ''
            
            poster = sel_response.css('.film-poster-img::attr(data-src), .film-poster-img::attr(src)').get()
            item['poster_url'] = response.urljoin(poster) if poster else ''
            
            # Get server buttons
            movie_page_url = self.driver.current_url
            server_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[data-id].link-item")
            
            if not server_buttons:
                self.logger.warning(f'   ⚠️  No servers found')
                self.stats['failed'] += 1
                return
            
            # Try first server and capture network requests
            try:
                first_button = server_buttons[0]
                server_name = first_button.text.strip()
                
                self.logger.info(f'   🔍 Clicking {server_name} and capturing network...')
                
                # Clear previous logs
                self.driver.get_log('performance')
                
                # Click server button
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", first_button)
                
                # Wait for iframe to load and network requests to complete
                time.sleep(8)
                
                # Capture network requests
                network_urls = self.get_network_requests()
                
                self.logger.info(f'   📡 Captured {len(network_urls)} network requests')
                
                # Find complete video URLs
                complete_url = None
                for url in network_urls:
                    if 'videostr.net' in url and '/e-1/' in url:
                        # Check if URL has complete parameters
                        if '?z=' in url:
                            z_param = url.split('?z=')[1].split('&')[0]
                            if len(z_param) > 10:
                                complete_url = url
                                self.logger.info(f'   ✅ Found complete URL from network!')
                                self.logger.info(f'      URL: {url[:100]}...')
                                break
                
                if complete_url:
                    item['stream_url'] = complete_url
                    item['server_name'] = server_name
                    item['quality'] = 'HD'
                    item['language'] = 'EN'
                    
                    self.stats['successful'] += 1
                    self.stats['network_captured'] += 1
                    yield item
                    return
                else:
                    self.logger.warning(f'   ❌ No complete URL found in network requests')
                    
            except Exception as e:
                self.logger.warning(f'   ⚠️  Error capturing network: {str(e)[:100]}')
            
            self.stats['failed'] += 1
            
        except Exception as e:
            self.logger.error(f'❌ Fatal error: {e}')
            self.stats['failed'] += 1
