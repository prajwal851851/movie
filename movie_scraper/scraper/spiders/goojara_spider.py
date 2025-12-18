# scraper/spiders/goojara_spider.py
"""
Spider for Goojara.to - scrapes movies and streaming links using Selenium
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

class GoojaraSpider(scrapy.Spider):
    name = 'goojara'
    allowed_domains = ['goojara.to', 'ww1.goojara.to']
    # Start with trend discovery pages - these contain links to genre/year categories
    start_urls = [
        'https://ww1.goojara.to/',
        'https://ww1.goojara.to/watch-trends-year',
        'https://ww1.goojara.to/watch-trends-genre',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1,
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
        self.logger.info('Initializing Selenium WebDriver...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info('✓ Selenium WebDriver initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=200, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.count = 0
        self.seen_urls = set()  # Track URLs we've already queued
        self.pages_scraped = {}  # Track pages scraped per URL
        self.category_urls_discovered = set()  # Track discovered category URLs
        self.is_first_parse = True  # Flag to discover categories on first parse

    def parse(self, response):
        """Parse movie listing page using Selenium with category discovery and pagination"""
        self.logger.info(f'Loading page with Selenium: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(5)  # Wait for page to load
            
            # Get rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract all links
            all_links = sel_response.css('a::attr(href)').getall()
            self.logger.info(f'Found {len(all_links)} total links')
            
            # If this is a trend discovery page, extract category URLs
            if 'watch-trends' in response.url and self.is_first_parse:
                self.is_first_parse = False
                category_pattern = re.compile(r'/watch-trends-(genre|year)-[\w-]+$')
                
                for link in all_links:
                    if link and category_pattern.search(link):
                        full_url = response.urljoin(link)
                        if full_url not in self.category_urls_discovered:
                            self.category_urls_discovered.add(full_url)
                            self.logger.info(f'Discovered category: {full_url}')
                            # Queue category page for scraping
                            yield scrapy.Request(
                                url=full_url,
                                callback=self.parse,
                                dont_filter=True
                            )
            
            # Find and queue movie links
            movies_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                # Filter for movie detail pages
                if link and re.match(r'^/m[a-zA-Z0-9]{5,7}$', link):
                    full_url = response.urljoin(link)
                    
                    # Skip if already seen
                    if full_url in self.seen_urls:
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
            
            # Try pagination for category pages
            if 'watch-trends-' in response.url and movies_found > 0 and self.count < self.limit:
                base_url = response.url.split('?')[0]
                if base_url not in self.pages_scraped:
                    self.pages_scraped[base_url] = 0
                
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
        self.logger.info(f'Parsing movie: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(2)  # Wait for page to load
            
            # Get rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            item = MovieItem()
            item['source_site'] = 'goojara.to'
            item['source_url'] = response.url
            
            # Extract movie ID from URL
            movie_id = response.url.split('/')[-1]
            item['imdb_id'] = f'goojara_{movie_id}'
            
            # Title - from h1
            title_text = sel_response.css('h1::text').get()
            if title_text:
                # Extract title and year from "Movie Name (2025)"
                title_match = re.match(r'(.+?)\s*\((\d{4})\)', title_text.strip())
                if title_match:
                    item['title'] = title_match.group(1).strip()
                    item['year'] = int(title_match.group(2))
                else:
                    item['title'] = title_text.strip()
                    item['year'] = None
            else:
                item['title'] = 'Unknown'
                item['year'] = None
            
            # Synopsis - from description paragraph
            synopsis = sel_response.xpath('//h1/following-sibling::text()').get()
            if synopsis:
                item['synopsis'] = synopsis.strip()
            else:
                item['synopsis'] = ''
            
            # Poster - try to find image
            poster = sel_response.css('img::attr(src)').get()
            if poster:
                item['poster_url'] = response.urljoin(poster)
            else:
                item['poster_url'] = ''
            
            # Extract streaming links from "Direct Links" section
            stream_links = sel_response.css('a[href*="/go.php"]')
            
            if stream_links:
                # Try to get actual streaming URL by navigating to go.php URLs
                actual_stream_url = None
                quality = 'HD'
                
                # Store the current URL to return to
                movie_page_url = self.driver.current_url
                
                # Try multiple links to find a working one
                # Priority: dood > luluvdo > others (skip Wootly and Vidsrc as they don't work)
                link_priority = []
                for link_elem in stream_links:
                    link_text = link_elem.css('::text').get()
                    link_href = link_elem.css('::attr(href)').get()
                    if link_text and link_href:
                        text_lower = link_text.lower()
                        # Skip Wootly and Vidsrc as they use embed pages that don't work
                        if 'wootly' in text_lower or 'vidsrc' in text_lower:
                            continue
                        # Prioritize dood and luluvdo
                        if 'dood' in text_lower:
                            priority = 0
                        elif 'luluvdo' in text_lower:
                            priority = 1
                        else:
                            priority = 2
                        link_priority.append((priority, link_href, link_text))
                
                # Sort by priority
                link_priority.sort(key=lambda x: x[0])
                
                if not link_priority:
                    self.logger.warning(f'No suitable streaming links found (all were Wootly/Vidsrc)')
                    return
                
                # Try first 3 links
                for i, (_, link_href, link_text) in enumerate(link_priority[:3]):
                    try:
                        # Determine quality from link text
                        if link_text:
                            if 'HD' in link_text.upper() or '1080' in link_text:
                                quality = 'HD'
                            elif '720' in link_text:
                                quality = '720p'
                            elif 'DVD' in link_text.upper():
                                quality = 'DVD'
                            else:
                                quality = 'SD'
                        
                        # Navigate directly to the go.php URL
                        full_link = response.urljoin(link_href)
                        self.logger.info(f'Navigating to: {link_text} - {full_link}')
                        
                        self.driver.get(full_link)
                        time.sleep(5)  # Wait for redirect
                        
                        # Get the final URL after redirect
                        final_url = self.driver.current_url
                        self.logger.info(f'Final URL: {final_url}')
                        
                        # Check if it's a valid streaming URL
                        invalid_patterns = ['goojara.to', '404', 'error', 'disable-devtool']
                        is_valid = (
                            final_url and 
                            len(final_url) > 20 and
                            not any(pattern in final_url.lower() for pattern in invalid_patterns)
                        )
                        
                        if is_valid:
                            # Use the streaming URL directly (dood, luluvdo, etc.)
                            actual_stream_url = final_url
                            self.logger.info(f'✓ Found valid streaming URL: {final_url[:60]}...')
                            break
                        else:
                            self.logger.warning(f'Invalid/blocked redirect URL: {final_url}')
                            
                    except Exception as e:
                        self.logger.warning(f'Failed to navigate to link {i+1}: {e}')
                        continue
                
                # Return to movie page
                try:
                    self.driver.get(movie_page_url)
                    time.sleep(1)
                except:
                    pass
                
                if actual_stream_url:
                    item['stream_url'] = actual_stream_url
                    item['quality'] = quality
                    item['language'] = 'EN'
                    
                    self.logger.info(f'✓ Successfully extracted: {item["title"]} ({item["year"]}) - {quality}')
                    yield item
                else:
                    self.logger.warning(f'✗ Could not extract real streaming URL for: {item["title"]}')
            else:
                self.logger.warning(f'✗ No streaming links found for: {item["title"]}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
