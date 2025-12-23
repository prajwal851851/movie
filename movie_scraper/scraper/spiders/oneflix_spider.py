# scraper/spiders/oneflix_spider.py
"""
Spider for 1Flix.to - scrapes movies and streaming links using Selenium
Uses UpCloud, MegaCloud, and VidCloud servers
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
from selenium.common.exceptions import TimeoutException
from scraper.items import MovieItem
import time
import re
import os
import django
from streaming.models import Movie

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

class OneFlixSpider(scrapy.Spider):
    name = 'oneflix'
    allowed_domains = ['1flix.to']
    start_urls = [
        'https://1flix.to/movie',
        'https://1flix.to/home',
        'https://1flix.to/genre/action',
        'https://1flix.to/genre/sci-fi-fantasy',
        'https://1flix.to/genre/thriller',
        'https://1flix.to/genre/horror',
        'https://1flix.to/genre/comedy',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium WebDriver"""
        self.logger.info('Initializing Selenium WebDriver for 1Flix...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info('✓ Selenium WebDriver initialized for 1Flix')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=100, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.count = 0
        self.seen_urls = set()
        self.pages_scraped = {}
        self.existing_movie_urls = set()
        self._load_existing_movies()

    def _load_existing_movies(self):
        """Load existing movies from the database to skip already scraped ones"""
        try:
            movies = Movie.objects.all().values_list('source_url', flat=True)
            for url in movies:
                if url:
                    self.existing_movie_urls.add(url)
            self.logger.info(f'Loaded {len(self.existing_movie_urls)} existing movies from DB')
        except Exception as e:
            self.logger.warning(f'Could not load existing movies: {e}')

    def parse(self, response):
        """Parse movie listing page using Selenium"""
        self.logger.info(f'Loading 1Flix page with Selenium: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(5)  # Wait for page to load
            
            # Scroll to load dynamic content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract all movie links
            all_links = sel_response.css('a::attr(href)').getall()
            self.logger.info(f'Found {len(all_links)} total links on page')
            
            # Find and queue movie detail pages
            movies_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                # Filter for movie detail pages (pattern: /movie/watch-{title}-{id})
                if link and re.match(r'^/movie/watch-[\w-]+-\d+', link):
                    full_url = response.urljoin(link)
                    
                    # Skip if already seen
                    if full_url in self.seen_urls:
                        continue
                    # Skip if movie already exists in DB
                    if full_url in self.existing_movie_urls:
                        self.logger.info(f'Skipping already scraped movie: {full_url}')
                        continue
                    
                    self.seen_urls.add(full_url)
                    movies_found += 1
                    self.count += 1
                    
                    self.logger.info(f'Queuing movie {self.count}: {full_url}')
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_movie,
                        dont_filter=True
                    )
            
            self.logger.info(f'Found {movies_found} new movies (Total: {self.count}/{self.limit})')
            
            # Try pagination
            if movies_found > 0 and self.count < self.limit:
                base_url = response.url.split('?')[0]
                if base_url not in self.pages_scraped:
                    self.pages_scraped[base_url] = 1
                
                current_page = self.pages_scraped[base_url]
                if current_page < self.max_pages:
                    next_page = current_page + 1
                    next_url = f"{base_url}?page={next_page}"
                    self.pages_scraped[base_url] = next_page
                    self.logger.info(f'Attempting pagination: {next_url}')
                    yield scrapy.Request(
                        url=next_url,
                        callback=self.parse,
                        dont_filter=True
                    )
            
        except Exception as e:
            self.logger.error(f'Error parsing with Selenium: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

    def parse_movie(self, response):
        """Parse individual movie page using Selenium"""
        self.logger.info(f'Parsing 1Flix movie: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(5)  # Wait for page to load
            
            # Scroll to ensure all content loads
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            item = MovieItem()
            item['source_site'] = '1flix.to'
            item['source_url'] = response.url
            
            # Extract movie ID from URL
            movie_id_match = re.search(r'-(\d+)$', response.url)
            movie_id = movie_id_match.group(1) if movie_id_match else response.url.split('/')[-1]
            item['imdb_id'] = f'1flix_{movie_id}'
            
            # Title - from h1 or title meta
            title_elem = sel_response.css('h1::text, h2.heading-name::text, .dp-i-c-poster .dp-i-c-title::text').get()
            if title_elem:
                # Extract title and year
                title_match = re.match(r'(.+?)\s*\((\d{4})\)', title_elem.strip())
                if title_match:
                    item['title'] = title_match.group(1).strip()
                    item['year'] = int(title_match.group(2))
                else:
                    item['title'] = title_elem.strip()
                    # Try to extract year from other elements
                    year_elem = sel_response.css('.dp-i-c-poster .dp-i-stats .item:first-child::text').get()
                    if year_elem and year_elem.isdigit():
                        item['year'] = int(year_elem)
                    else:
                        item['year'] = None
            else:
                item['title'] = 'Unknown'
                item['year'] = None
            
            # Synopsis - from description
            synopsis = sel_response.css('.description::text, .dp-i-c-poster .description::text, p.description::text').get()
            if synopsis:
                item['synopsis'] = synopsis.strip()
            else:
                item['synopsis'] = ''
            
            # Poster - try to find image
            poster = sel_response.css('.dp-i-c-poster .film-poster-img::attr(src), img.film-poster-img::attr(src), .poster img::attr(src)').get()
            if poster:
                item['poster_url'] = response.urljoin(poster)
            else:
                item['poster_url'] = ''
            
            # Extract streaming server links (UpCloud, MegaCloud, VidCloud)
            # Look for server buttons or data-id attributes
            server_links = []
            
            # Try to find server buttons
            server_buttons = sel_response.css('ul.server-list li, .servers .server-item, .episodes-servers .item')
            
            if not server_buttons:
                # Try alternative selectors
                server_buttons = sel_response.css('[data-id], [data-linkid]')
            
            # Store the current URL to return to
            movie_page_url = self.driver.current_url
            
            # Priority for servers: UpCloud > MegaCloud > VidCloud
            server_priority = {'upcloud': 0, 'megacloud': 1, 'vidcloud': 2}
            
            # Extract server information
            servers_info = []
            for button in server_buttons:
                server_name = button.css('::text, a::text').get()
                server_id = button.css('::attr(data-id), ::attr(data-linkid)').get()
                
                if server_name:
                    server_name_lower = server_name.lower().strip()
                    priority = server_priority.get(server_name_lower, 3)
                    servers_info.append((priority, server_name, server_id, button))
            
            # Sort by priority
            servers_info.sort(key=lambda x: x[0])
            
            if not servers_info:
                self.logger.warning(f'No streaming servers found for: {item["title"]}')
                return
            
            # Try to extract streaming URL from top 3 servers
            actual_stream_url = None
            quality = 'HD'
            server_name = 'Unknown'
            
            for i, (priority, srv_name, srv_id, button_elem) in enumerate(servers_info[:3]):
                try:
                    self.logger.info(f'Trying server: {srv_name}')
                    
                    # Click the server button to load the video
                    try:
                        # Try to find and click the button
                        button = self.driver.find_element(By.CSS_SELECTOR, f'[data-id="{srv_id}"]')
                        button.click()
                        time.sleep(5)  # Wait for video player to load
                    except:
                        # Alternative: navigate to the embed URL directly
                        self.logger.info(f'Could not click button, trying alternative method')
                        continue
                    
                    # Look for iframe src
                    try:
                        iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe.embed-player, iframe#iframe-embed, iframe[src*="embed"]')
                        iframe_src = iframe.get_attribute('src')
                        
                        if iframe_src and len(iframe_src) > 20:
                            self.logger.info(f'Found iframe source: {iframe_src[:60]}...')
                            
                            # Navigate to the iframe to get the actual stream URL
                            self.driver.get(iframe_src)
                            time.sleep(5)
                            
                            final_url = self.driver.current_url
                            
                            # Check if it's a valid streaming URL
                            invalid_patterns = ['404', 'error', 'refused', 'denied']
                            is_valid = (
                                final_url and 
                                len(final_url) > 20 and
                                not any(pattern in final_url.lower() for pattern in invalid_patterns)
                            )
                            
                            if is_valid:
                                actual_stream_url = final_url
                                server_name = srv_name
                                
                                # Extract quality if available
                                if 'hd' in srv_name.lower() or '1080' in srv_name.lower():
                                    quality = 'HD'
                                elif '720' in srv_name.lower():
                                    quality = '720p'
                                else:
                                    quality = 'SD'
                                
                                self.logger.info(f'✓ Found valid streaming URL from {server_name}: {final_url[:60]}...')
                                break
                    except Exception as iframe_e:
                        self.logger.warning(f'Could not extract iframe: {iframe_e}')
                        continue
                    
                except Exception as e:
                    self.logger.warning(f'Failed to extract from server {srv_name}: {e}')
                    continue
            
            # Return to movie page
            try:
                self.driver.get(movie_page_url)
                time.sleep(1)
            except:
                pass
            
            if actual_stream_url:
                item['stream_url'] = actual_stream_url
                item['server_name'] = server_name
                item['quality'] = quality
                item['language'] = 'EN'
                
                self.logger.info(f'✓ Successfully extracted: {item["title"]} ({item["year"]}) - {server_name} - {quality}')
                yield item
            else:
                self.logger.warning(f'✗ Could not extract streaming URL for: {item["title"]}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
            import traceback
            self.logger.error(traceback.format_exc())