# scraper/scraper/spiders/improved_makemovies_spider.py
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scraper.items import MovieItem
import time
import re
import logging

class ImprovedMakemoviesSpider(scrapy.Spider):
    name = 'improved_makemovies'
    allowed_domains = ['worldfreemovies.xyz', '123movies.com']
    start_urls = ['https://worldfreemovies.xyz/']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'LOG_LEVEL': 'INFO',
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium with robust configuration"""
        self.logger.info('Initializing Selenium WebDriver...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Updated headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # More realistic user agent
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            # Hide webdriver detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                '''
            })
            
            self.logger.info('✓ Selenium WebDriver initialized successfully')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=20, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0

    def parse(self, response):
        """Parse homepage to find movie links"""
        self.logger.info(f'Loading page: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for movie items to load
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.film_list-wrap')))
                self.logger.info('✓ Content loaded')
            except TimeoutException:
                self.logger.warning('Timeout waiting for content')
            
            # Extra wait for JavaScript
            time.sleep(3)
            
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get the rendered HTML
            html = self.driver.page_source
            
            # Create Scrapy response from rendered HTML
            sel_response = HtmlResponse(
                url=response.url, 
                body=html.encode('utf-8'), 
                encoding='utf-8'
            )
            
            # Extract movie links
            movie_links = sel_response.css('div.film_list-wrap div.flw-item a.film-poster::attr(href)').getall()
            
            if not movie_links:
                # Try alternative selectors
                movie_links = sel_response.css('a[href*="/movie/"]::attr(href)').getall()
            
            self.logger.info(f'Found {len(movie_links)} movie links')
            
            if not movie_links:
                self.logger.error('No movie links found!')
                return
            
            # Process movie links
            for link in movie_links[:self.limit]:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                    
                full_url = response.urljoin(link)
                self.count += 1
                self.logger.info(f'Queuing movie {self.count}: {full_url}')
                yield scrapy.Request(
                    url=full_url, 
                    callback=self.parse_movie_page,
                    dont_filter=True
                )
            
        except Exception as e:
            self.logger.error(f'Error parsing homepage: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

    def parse_movie_page(self, response):
        """Parse individual movie page to extract details and streaming link"""
        self.logger.info(f'Parsing movie page: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            # Wait for page to load - try multiple selectors
            wait = WebDriverWait(self.driver, 15)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.heading-name')))
            except TimeoutException:
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
                except TimeoutException:
                    self.logger.warning('Timeout waiting for title element')
            
            # Wait for player iframe to load
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract movie information
            item = MovieItem()
            item['source_site'] = '123movies.com'
            item['source_url'] = response.url
            
            # Title
            title = sel_response.css('h2.heading-name a::text').get()
            if not title:
                title = sel_response.css('h2.heading-name::text').get()
            
            item['title'] = title.strip() if title else 'Unknown Title'
            
            # IMDB ID - extract from URL pattern
            url_match = re.search(r'/movie/([^/]+)-([^/]+)W/', response.url)
            if url_match:
                imdb_id = url_match.group(2)  # The numeric ID
            else:
                imdb_id = f'123m_{hash(response.url)}'
            
            item['imdb_id'] = f'123movies_{imdb_id}'
            
            # Year - extract from title or metadata
            year = None
            year_text = sel_response.css('div.elements div.row-line:contains("Released:") *::text').getall()
            if year_text:
                year_str = ' '.join(year_text)
                year_match = re.search(r'(20\d{2}|19\d{2})', year_str)
                if year_match:
                    year = int(year_match.group(1))
            
            if not year:
                # Try from title
                title_str = str(item['title'])
                year_match = re.search(r'\((20\d{2}|19\d{2})\)', title_str)
                if year_match:
                    year = int(year_match.group(1))
            
            item['year'] = year
            
            # Synopsis
            synopsis = sel_response.css('div.description::text').get()
            if not synopsis:
                synopsis = sel_response.xpath('//meta[@property="og:description"]/@content').get()
            
            item['synopsis'] = synopsis.strip() if synopsis else ''
            
            # Poster
            poster = sel_response.css('div.film-poster img::attr(src)').get()
            if not poster:
                poster = sel_response.xpath('//meta[@property="og:image"]/@content').get()
            
            item['poster_url'] = poster if poster else ''
            
            # Stream URL - Extract iframe embed URL
            stream_url = None
            
            # Method 1: Find iframe in player
            iframe_url = sel_response.css('div#iframe-embed iframe::attr(src)').get()
            if not iframe_url:
                iframe_url = sel_response.css('iframe[id*="iframe"]::attr(src)').get()
            if not iframe_url:
                iframe_url = sel_response.css('iframe::attr(src)').get()
            
            if iframe_url:
                self.logger.info(f'Found iframe: {iframe_url}')
                stream_url = iframe_url
            
            # Method 2: Look for data-src attribute
            if not stream_url:
                stream_url = sel_response.css('iframe::attr(data-src)').get()
            
            # Method 3: Search in JavaScript for embed URLs
            if not stream_url:
                patterns = [
                    r'"embedUrl"\s*:\s*"([^"]+)"',
                    r'iframe.*?src="([^"]+)"',
                    r'player_iframe.*?"([^"]+)"',
                ]
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        stream_url = match.group(1)
                        self.logger.info(f'Found stream URL in source: {pattern}')
                        break
            
            if stream_url:
                # Clean URL
                stream_url = stream_url.strip()
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                elif stream_url.startswith('/'):
                    stream_url = response.urljoin(stream_url)
                
                # Decode if URL encoded
                if '%' in stream_url:
                    from urllib.parse import unquote
                    stream_url = unquote(stream_url)
                
                item['stream_url'] = stream_url
                item['quality'] = 'HD'
                item['language'] = 'EN'
                
                self.logger.info(f'✓ Successfully extracted: {item["title"]}\nStream: {stream_url}')
                yield item
            else:
                self.logger.warning(f'✗ No stream URL found for: {item["title"]}')
                # Still yield without stream URL
                item['stream_url'] = ''
                item['quality'] = 'N/A'
                item['language'] = 'EN'
                yield item
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page {response.url}: {e}')
            import traceback
            self.logger.error(traceback.format_exc())