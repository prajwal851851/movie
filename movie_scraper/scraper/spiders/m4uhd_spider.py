import scrapy
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from scraper.items import MovieItem
import time
import re

class M4uhdSpider(scrapy.Spider):
    name = 'm4uhd'
    allowed_domains = ['m4uhd.to', 'ww1.m4uhd.to']
    # Start with homepage and genre pages
    start_urls = [
        'https://ww1.m4uhd.to/home',
        'https://ww1.m4uhd.to/genre/action',
        'https://ww1.m4uhd.to/genre/comedy',
        'https://ww1.m4uhd.to/genre/drama',
        'https://ww1.m4uhd.to/genre/thriller',
        'https://ww1.m4uhd.to/genre/horror',
        'https://ww1.m4uhd.to/genre/sci-fi',
        'https://ww1.m4uhd.to/genre/adventure',
        'https://ww1.m4uhd.to/genre/romance',
        'https://ww1.m4uhd.to/genre/crime',
        'https://ww1.m4uhd.to/genre/fantasy',
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
        crawler.signals.connect(spider.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        self.logger.info('Initializing Selenium WebDriver...')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.logger.info('✓ Selenium WebDriver initialized')

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0
        self.seen_urls = set()  # Track URLs we've already queued
        self.pages_scraped = {}  # Track which pages we've scraped for each section

    def parse(self, response):
        """Parse movie listing page using Selenium"""
        # Determine which section this is
        section = response.url
        
        # Get current page number for this section
        if section not in self.pages_scraped:
            self.pages_scraped[section] = 1
        
        page_num = self.pages_scraped[section]
        
        # Construct URL with page number
        if page_num == 1:
            url = section
        else:
            # M4uHD pagination format: /home/page/2, /genre/action/page/2, etc.
            url = f"{section}/page/{page_num}"
        
        self.logger.info(f'Loading page {page_num} from {section}')
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Get rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract movie links using specific selectors for M4uHD
            # Try different selectors that might contain movie links
            movie_links_css = [
                'article.item a::attr(href)',
                'div.movie-item a::attr(href)',
                'div.film-poster a::attr(href)',
                '.flw-item a::attr(href)',
                'a.movie-link::attr(href)',
                'div.post a::attr(href)',
            ]
            
            all_links = []
            for selector in movie_links_css:
                links = sel_response.css(selector).getall()
                if links:
                    all_links.extend(links)
                    self.logger.info(f'Found {len(links)} links with selector: {selector}')
            
            # Fallback to all links if no specific selectors worked
            if not all_links:
                all_links = sel_response.css('a::attr(href)').getall()
                self.logger.info(f'Using fallback: Found {len(all_links)} total links on page')
            
            # Log some sample links to understand the pattern
            if page_num == 1:
                sample_links = all_links[:30]
                self.logger.info(f'Sample links from {section}: {sample_links}')
            
            movies_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                # Filter for movie detail pages
                # M4uHD pattern: watch-[ID]-[movie-name]-[year].html
                is_movie = False
                if link and isinstance(link, str):
                    if re.match(r'^watch-[a-z0-9]+-[\w\-]+\.html$', link):
                        is_movie = True
                
                if is_movie:
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
            
            self.logger.info(f'Found {movies_found} new movies from page {page_num} (Total: {self.count}/{self.limit})')
            
            # If we found movies and haven't reached limit, try next page
            if movies_found > 0 and self.count < self.limit:
                self.pages_scraped[section] += 1
                yield scrapy.Request(
                    url=section,
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
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            item = MovieItem()
            
            # Extract movie ID from URL (e.g., watch-iodyw0-avatar-fire-and-ash-2025.html)
            url_match = re.search(r'watch-([a-z0-9]+)-', response.url)
            if url_match:
                movie_id = url_match.group(1)
            else:
                # Fallback to hash if pattern doesn't match
                movie_id = f'{hash(response.url)}'
            item['imdb_id'] = f'm4uhd_{movie_id}'
            
            # Extract title
            title = sel_response.css('h1.entry-title::text').get()
            if not title:
                title = sel_response.css('h1::text').get()
            if not title:
                title = sel_response.css('title::text').get()
            
            if title:
                title = title.strip()
                # Remove year from title if present
                title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
                item['title'] = title
            else:
                self.logger.warning(f'No title found for {response.url}')
                return
            
            # Extract year
            year_text = sel_response.css('span.date::text').get()
            if not year_text:
                year_text = sel_response.css('.year::text').get()
            if year_text:
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    item['year'] = int(year_match.group(1))
            
            if 'year' not in item:
                item['year'] = 2024
            
            # Extract synopsis
            synopsis = sel_response.css('div.description::text').get()
            if not synopsis:
                synopsis = sel_response.css('div.entry-content p::text').get()
            if not synopsis:
                synopsis = sel_response.css('p::text').get()
            
            item['synopsis'] = synopsis.strip() if synopsis else f'{title} - Watch online'
            
            # Extract poster
            poster = sel_response.css('div.poster img::attr(src)').get()
            if not poster:
                poster = sel_response.css('img.thumbnail::attr(src)').get()
            if not poster:
                poster = sel_response.css('meta[property="og:image"]::attr(content)').get()
            
            item['poster_url'] = poster if poster else ''
            
            # Source site and URL
            item['source_site'] = 'm4uhd.to'
            item['source_url'] = response.url
            
            # Extract streaming links - look for server/player links
            stream_links = sel_response.css('div.server a::attr(href)').getall()
            if not stream_links:
                stream_links = sel_response.css('div.player a::attr(href)').getall()
            if not stream_links:
                stream_links = sel_response.css('a[data-server]::attr(href)').getall()
            
            # Try to find iframe sources
            if not stream_links:
                iframes = sel_response.css('iframe::attr(src)').getall()
                stream_links = [iframe for iframe in iframes if iframe and 'http' in iframe]
            
            # Look for embed URLs in the page
            if not stream_links:
                # Search for common embed patterns in the HTML
                embed_patterns = [
                    r'https?://[^"\']+(?:embed|player|stream)[^"\']+',
                    r'https?://(?:dood|myvidplay|vidsrc|upstream)[^"\']+',
                ]
                for pattern in embed_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        stream_links.extend(matches)
                        break
            
            if stream_links:
                # Prioritize certain providers
                preferred_providers = ['dood', 'myvidplay', 'upstream']
                
                # Sort links by preference
                def get_priority(url):
                    for i, provider in enumerate(preferred_providers):
                        if provider in url.lower():
                            return i
                    return len(preferred_providers)
                
                stream_links.sort(key=get_priority)
                
                # Use the first (best) link
                stream_url = stream_links[0]
                
                # Clean URL
                stream_url = stream_url.strip()
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                elif stream_url.startswith('/'):
                    stream_url = response.urljoin(stream_url)
                
                # Follow redirect if needed
                if stream_url.startswith('http'):
                    # Try to navigate and get final URL
                    try:
                        original_window = self.driver.current_window_handle
                        self.driver.execute_script(f"window.open('{stream_url}', '_blank');")
                        time.sleep(3)
                        
                        # Switch to new tab
                        for window_handle in self.driver.window_handles:
                            if window_handle != original_window:
                                self.driver.switch_to.window(window_handle)
                                break
                        
                        final_url = self.driver.current_url
                        
                        # Close tab and switch back
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                        
                        # Validate URL
                        invalid_patterns = [
                            'disable-devtool',
                            '404',
                            'not-found',
                            'error'
                        ]
                        
                        if not any(pattern in final_url.lower() for pattern in invalid_patterns):
                            stream_url = final_url
                            self.logger.info(f'✓ Found valid streaming URL: {stream_url[:50]}...')
                        else:
                            self.logger.warning(f'Invalid URL detected: {final_url}')
                            stream_url = stream_links[0]  # Use original
                    
                    except Exception as e:
                        self.logger.warning(f'Could not follow redirect: {e}')
                
                item['stream_url'] = stream_url
                item['quality'] = 'HD'
                item['language'] = 'EN'
                
                self.logger.info(f'✓ Successfully extracted: {item["title"]} ({item["year"]}) - {item["quality"]}')
                yield item
            else:
                self.logger.warning(f'✗ No stream URL found for: {item["title"]}')
                # Still yield without stream URL
                item['stream_url'] = ''
                item['quality'] = 'N/A'
                item['language'] = 'EN'
                yield item
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
            import traceback
            self.logger.error(traceback.format_exc())
