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
    start_urls = ['https://ww1.goojara.to/watch-movies']
    
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

    def __init__(self, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0

    def parse(self, response):
        """Parse movie listing page using Selenium"""
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
            
            # Extract all links from the rendered page
            all_links = sel_response.css('a::attr(href)').getall()
            self.logger.info(f'Found {len(all_links)} total links on page')
            
            movie_links_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                # Filter for movie detail pages (pattern: /mXXXXX - 5-7 alphanumeric chars)
                if link and re.match(r'^/m[a-zA-Z0-9]{5,7}$', link):
                    movie_links_found += 1
                    full_url = response.urljoin(link)
                    self.count += 1
                    self.logger.info(f'Queuing movie {self.count}: {full_url}')
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_movie,
                        dont_filter=True
                    )
            
            self.logger.info(f'Found {movie_links_found} movie links matching pattern')
            
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
