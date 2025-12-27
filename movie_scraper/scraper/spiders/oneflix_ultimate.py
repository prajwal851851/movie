# scraper/spiders/oneflix_ultimate.py
"""
ULTIMATE 1Flix Spider - Best of all solutions combined
✓ Real-time link validation during scraping
✓ Multiple server fallback (UpCloud → MegaCloud → VidCloud)
✓ Smart retry logic
✓ Detailed logging and success tracking
✓ Filters out broken links automatically
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
from webdriver_manager.chrome import ChromeDriverManager
from scraper.items import MovieItem
import time
import re
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie

class OneFlixUltimateSpider(scrapy.Spider):
    name = 'oneflix_ultimate'
    allowed_domains = ['1flix.to']
    start_urls = [
        'https://1flix.to/top-imdb',  # Start with top-rated movies
        'https://1flix.to/movie',
        'https://1flix.to/genre/action',
        'https://1flix.to/genre/thriller',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, limit=100, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.count = 0
        self.seen_urls = set()
        self.pages_scraped = {}
        self.existing_movie_urls = set()
        
        # Statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'broken_links': 0,
            'working_links': 0
        }
        
        self._load_existing_movies()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium WebDriver with optimized settings"""
        self.logger.info('🚀 Initializing Ultimate 1Flix Spider...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info('✓ Selenium WebDriver initialized')
        except Exception as e:
            self.logger.error(f'❌ Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        """Cleanup and show final statistics"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        
        self.logger.info('\n' + '='*70)
        self.logger.info('🎬 SCRAPING SUMMARY - 1FLIX ULTIMATE SPIDER')
        self.logger.info('='*70)
        self.logger.info(f'Movies Attempted:    {self.stats["attempted"]}')
        self.logger.info(f'✓ Successful:        {self.stats["successful"]} ({self._percent(self.stats["successful"], self.stats["attempted"])})')
        self.logger.info(f'✗ Failed:            {self.stats["failed"]} ({self._percent(self.stats["failed"], self.stats["attempted"])})')
        self.logger.info(f'📊 Working Links:    {self.stats["working_links"]}')
        self.logger.info(f'🚫 Broken Links:     {self.stats["broken_links"]} (filtered out)')
        self.logger.info('='*70 + '\n')

    def _percent(self, part, total):
        """Calculate percentage"""
        return f'{(part/max(total,1)*100):.1f}%'

    def _load_existing_movies(self):
        """Load existing movies to avoid duplicates"""
        try:
            movies = Movie.objects.all().values_list('source_url', flat=True)
            self.existing_movie_urls = set(url for url in movies if url)
            self.logger.info(f'📚 Loaded {len(self.existing_movie_urls)} existing movies')
        except Exception as e:
            self.logger.warning(f'⚠️  Could not load existing movies: {e}')

    def quick_validate_url(self, url):
        """
        FAST validation - checks URL structure and basic patterns
        Returns: (is_valid, reason)
        """
        if not url or len(url) < 30:
            return False, "URL too short"
        
        # Check for obvious error patterns
        invalid_patterns = ['404', 'error', 'denied', 'blocked', 'recaptcha', 'captcha']
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False, "Invalid pattern in URL"
        
        # VideoStr.net specific checks (strict)
        if 'videostr.net' in url:
            if not re.search(r'/e-1/[A-Za-z0-9_-]+\?z=', url):
                return False, "Invalid VideoStr format"
            # Check if z= parameter has a value (not empty)
            if '?z=' in url:
                z_param = url.split('?z=')[1].split('&')[0]
                if len(z_param) < 10:
                    return False, "Incomplete URL parameters (z= is empty or too short)"
        
        # For other servers (MegaCloud, VidCloud, etc.), just check basic structure
        # They might have different URL patterns
        
        return True, "Passed quick validation"

    def deep_validate_url(self, url):
        """
        DEEP validation - actually checks if link works
        Returns: (is_valid, reason)
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://1flix.to/'
            }
            
            # HEAD request first (faster)
            response = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
            
            if response.status_code >= 400:
                return False, f"HTTP {response.status_code}"
            
            # Check for error redirects
            if 'error' in response.url.lower() or '404' in response.url:
                return False, "Redirected to error page"
            
            # For suspicious 200s, do GET request to check content
            if response.status_code == 200 and 'videostr.net' in url:
                try:
                    # Quick GET to check for error messages
                    get_response = requests.get(url, headers=headers, timeout=10)
                    content = get_response.text.lower()
                    
                    # Common error messages on video sites
                    error_phrases = [
                        "we're sorry",
                        "can't find the file",
                        "file not found",
                        "removed due a copyright",
                        "deleted by owner",
                        "video not found",
                        "file has been removed"
                    ]
                    
                    if any(phrase in content for phrase in error_phrases):
                        return False, "Error message on page"
                    
                    # Look for good signs (video player)
                    if 'player' in content or 'video' in content:
                        return True, "Video player detected"
                        
                except requests.Timeout:
                    # Timeout on GET, but HEAD worked - assume valid
                    return True, "HEAD OK (GET timeout)"
            
            return True, f"HTTP {response.status_code}"
            
        except requests.Timeout:
            return False, "Request timeout"
        except requests.RequestException as e:
            return False, f"Network error"
        except Exception as e:
            return False, "Validation error"

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
                
                if link and re.match(r'^/movie/watch-[\w-]+-\d+', link):
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
        """Parse individual movie with smart validation"""
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
            
            movie_id_match = re.search(r'-(\d+)$', response.url)
            movie_id = movie_id_match.group(1) if movie_id_match else response.url.split('/')[-1]
            item['imdb_id'] = f'1flix_{movie_id}'
            
            # Title and year
            title_elem = sel_response.css('h2.heading-name a::text, .film-name::text').get()
            if not title_elem:
                self.logger.warning(f'⚠️  No title found, skipping: {response.url}')
                self.stats['failed'] += 1
                return
            
            title_text = re.sub(r'^Watch\s+', '', title_elem.strip(), flags=re.IGNORECASE)
            title_text = re.sub(r'\s+Online\s+free$', '', title_text, flags=re.IGNORECASE)
            
            title_match = re.search(r'(.+?)\s+(\d{4})', title_text)
            if title_match:
                item['title'] = title_match.group(1).strip()
                item['year'] = int(title_match.group(2))
            else:
                item['title'] = title_text
                item['year'] = None
            
            self.logger.info(f'\n🎬 Processing: {item["title"]} ({item["year"]})')
            
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
            
            # Prioritize servers: UpCloud > MegaCloud > VidCloud
            server_priority = {'upcloud': 0, 'megacloud': 1, 'vidcloud': 2}
            servers_info = []
            
            for button in server_buttons:
                try:
                    server_name = button.text.strip()
                    server_id = button.get_attribute('data-id')
                    if server_name and server_id:
                        priority = server_priority.get(server_name.lower(), 3)
                        servers_info.append((priority, server_name, server_id, button))
                        self.logger.info(f'   📡 Found server: {server_name}')
                except:
                    continue
            
            servers_info.sort(key=lambda x: x[0])
            
            # Try each server until we find a working link
            for priority, srv_name, srv_id, _ in servers_info[:3]:  # Try top 3
                try:
                    self.logger.info(f'   🔍 Testing {srv_name}...')
                    
                    # Re-find the button to avoid stale element reference
                    try:
                        button_elem = self.driver.find_element(By.CSS_SELECTOR, f"a[data-id='{srv_id}'].link-item")
                    except:
                        self.logger.warning(f'      ⚠️  Could not find button for {srv_name}')
                        continue
                    
                    # Click server button
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button_elem)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", button_elem)
                    time.sleep(5)
                    
                    # Find iframe and wait for it to fully load
                    iframe = None
                    for selector in ["iframe#iframe-embed", "iframe[src*='embed']", "iframe[src]"]:
                        try:
                            iframe = WebDriverWait(self.driver, 8).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            if iframe:
                                break
                        except:
                            continue
                    
                    if not iframe:
                        self.logger.warning(f'      ⚠️  No iframe found')
                        continue
                    
                    # Wait additional time for JavaScript to populate the iframe src fully
                    time.sleep(3)
                    
                    # Get iframe src - try multiple times as it may be dynamically loaded
                    iframe_src = None
                    for attempt in range(3):
                        iframe_src = iframe.get_attribute('src')
                        # For videostr, check if z= has a value
                        if iframe_src and 'videostr.net' in iframe_src:
                            if '?z=' in iframe_src and len(iframe_src.split('?z=')[1]) > 5:
                                break
                        # For other servers, just check if URL looks reasonable
                        elif iframe_src and len(iframe_src) > 30:
                            break
                        time.sleep(2)
                    
                    if not iframe_src or len(iframe_src) < 20:
                        self.logger.warning(f'      ⚠️  Invalid iframe src')
                        continue
                    
                    self.logger.info(f'      📎 Extracted URL: {iframe_src[:80]}...')
                    
                    # QUICK VALIDATION (instant)
                    quick_valid, quick_reason = self.quick_validate_url(iframe_src)
                    if not quick_valid:
                        self.logger.warning(f'      ❌ Quick check failed: {quick_reason}')
                        self.stats['broken_links'] += 1
                        continue
                    
                    # DEEP VALIDATION (checks if actually works)
                    self.logger.info(f'      ⏳ Deep validating...')
                    deep_valid, deep_reason = self.deep_validate_url(iframe_src)
                    
                    if deep_valid:
                        item['stream_url'] = iframe_src
                        item['server_name'] = srv_name
                        item['quality'] = 'HD'
                        item['language'] = 'EN'
                        
                        self.logger.info(f'      ✅ WORKING LINK! ({deep_reason})')
                        self.stats['successful'] += 1
                        self.stats['working_links'] += 1
                        yield item
                        return
                    else:
                        self.logger.warning(f'      ❌ Link broken: {deep_reason}')
                        self.stats['broken_links'] += 1
                        
                except Exception as e:
                    self.logger.warning(f'      ⚠️  Error with {srv_name}: {str(e)[:100]}')
                finally:
                    try:
                        self.driver.get(movie_page_url)
                        time.sleep(2)
                    except:
                        pass
            
            self.logger.warning(f'   ❌ No working links found for: {item["title"]}')
            self.stats['failed'] += 1
            
        except Exception as e:
            self.logger.error(f'❌ Fatal error: {e}')
            self.stats['failed'] += 1
