# scraper/spiders/goojara_spider_v2.py
"""
Enhanced Goojara spider with multi-server support and smart scraping.
Supports: Dood, Wootly, and other streaming servers
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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink

class GoojaraSpiderV2(scrapy.Spider):
    name = 'goojara_v2'
    allowed_domains = ['goojara.to', 'ww1.goojara.to']
    start_urls = [
        'https://ww1.goojara.to/watch-trends-genre',
        'https://ww1.goojara.to/watch-movies-genre-Action',
        'https://ww1.goojara.to/watch-trends-year-2025',
        'https://ww1.goojara.to/watch-trends-year-2024'
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
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

    def __init__(self, limit=200, max_pages=5, rescrape_broken=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.rescrape_broken = rescrape_broken
        self.count = 0
        self.seen_urls = set()
        self.pages_scraped = {}
        self.category_urls_discovered = set()
        self.is_first_parse = True
        
        # Load existing movies from database to skip already scraped ones
        self.existing_movie_urls = set()
        self.broken_link_movies = set()
        self._load_existing_movies()

    def _load_existing_movies(self):
        """Load existing movies from database to optimize scraping"""
        try:
            # Get all existing movie source URLs
            existing_movies = Movie.objects.all().values('source_url', 'imdb_id')
            for movie in existing_movies:
                if movie['source_url']:
                    self.existing_movie_urls.add(movie['source_url'])
            
            # Get movies with broken links (need re-scraping)
            if self.rescrape_broken:
                broken_links = StreamingLink.objects.filter(
                    is_active=False
                ).values_list('movie__source_url', flat=True).distinct()
                
                for url in broken_links:
                    if url:
                        self.broken_link_movies.add(url)
                
                # Also check for specific error messages
                error_patterns = [
                    'Not Found',
                    'video you are looking for is not found',
                    'media could not be loaded',
                    'server or network failed',
                    'format is not supported'
                ]
                
                for pattern in error_patterns:
                    broken = StreamingLink.objects.filter(
                        error_message__icontains=pattern
                    ).values_list('movie__source_url', flat=True).distinct()
                    
                    for url in broken:
                        if url:
                            self.broken_link_movies.add(url)
            
            self.logger.info(f'Loaded {len(self.existing_movie_urls)} existing movies')
            self.logger.info(f'Found {len(self.broken_link_movies)} movies with broken links to re-scrape')
            
        except Exception as e:
            self.logger.warning(f'Could not load existing movies: {e}')

    def parse(self, response):
        """Parse movie listing page using Selenium with category discovery and pagination"""
        self.logger.info(f'Loading page with Selenium: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            all_links = sel_response.css('a::attr(href)').getall()
            self.logger.info(f'Found {len(all_links)} total links')
            
            # Category discovery disabled - only scrape specified years
            # if 'watch-trends' in response.url and self.is_first_parse:
            #     self.is_first_parse = False
            #     category_pattern = re.compile(r'/watch-trends-(genre|year)-[\w-]+$')
            #     
            #     for link in all_links:
            #         if link and category_pattern.search(link):
            #             full_url = response.urljoin(link)
            #             if full_url not in self.category_urls_discovered:
            #                 self.category_urls_discovered.add(full_url)
            #                 self.logger.info(f'Discovered category: {full_url}')
            #                 yield scrapy.Request(
            #                     url=full_url,
            #                     callback=self.parse,
            #                     dont_filter=True
            #                 )
            
            # Find and queue movie links
            movies_found = 0
            for link in all_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                if link and re.match(r'^/m[a-zA-Z0-9]{5,7}$', link):
                    full_url = response.urljoin(link)
                    
                    # Skip if already seen in this session
                    if full_url in self.seen_urls:
                        continue
                    
                    # Smart scraping: Skip if already in DB and not broken
                    if full_url in self.existing_movie_urls and full_url not in self.broken_link_movies:
                        self.logger.info(f'Skipping already scraped movie: {full_url}')
                        continue
                    
                    self.seen_urls.add(full_url)
                    movies_found += 1
                    self.count += 1
                    
                    if full_url in self.broken_link_movies:
                        self.logger.info(f'Re-scraping broken link movie {self.count}: {full_url}')
                    else:
                        self.logger.info(f'Queuing new movie {self.count}: {full_url}')
                    
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_movie,
                        dont_filter=True
                    )
            
            self.logger.info(f'Found {movies_found} new/broken movies (Total: {self.count}/{self.limit})')
            
            # Pagination
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
        """Parse individual movie page and extract ALL available streaming servers"""
        self.logger.info(f'Parsing movie: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(2)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract basic movie info
            movie_id = response.url.split('/')[-1]
            imdb_id = f'goojara_{movie_id}'
            
            title_text = sel_response.css('h1::text').get()
            if title_text:
                title_match = re.match(r'(.+?)\s*\((\d{4})\)', title_text.strip())
                if title_match:
                    title = title_match.group(1).strip()
                    year = int(title_match.group(2))
                else:
                    title = title_text.strip()
                    year = None
            else:
                title = 'Unknown'
                year = None
            
            synopsis = sel_response.xpath('//h1/following-sibling::text()').get()
            synopsis = synopsis.strip() if synopsis else ''
            
            poster = sel_response.css('img::attr(src)').get()
            poster_url = response.urljoin(poster) if poster else ''
            
            # Extract ALL streaming links
            stream_links = sel_response.css('a[href*="/go.php"]')
            
            if not stream_links:
                self.logger.warning(f'No streaming links found for: {title}')
                return
            
            # Organize links by server type
            server_links = {
                'wootly': [],
                'dood': []
                
            }
            
            for link_elem in stream_links:
                link_text = link_elem.css('::text').get()
                link_href = link_elem.css('::attr(href)').get()
                
                if not link_text or not link_href:
                    continue
                
                text_lower = link_text.lower()
                
                # Categorize by server type
                if 'dood' in text_lower:
                    server_links['dood'].append((link_href, link_text, 'Dood'))
                elif 'luluvdo' in text_lower or 'lulustream' in text_lower:
                    # Skip luluvdo links completely
                    continue
                elif 'vidsrc' in text_lower:
                    # Skip vidsrc links completely
                    continue
                elif 'wootly' in text_lower:
                    server_links['wootly'].append((link_href, link_text, 'Wootly'))
                else:
                    # Skip unknown servers completely
                    continue
            
            # Extract streaming URLs from each server (prioritize Dood, then others)
            all_streaming_links = []
            movie_page_url = self.driver.current_url
            
            # Process servers in priority order
            for server_type in ['dood', 'wootly']:
                for link_href, link_text, server_name in server_links[server_type]:
                    try:
                        quality = self._extract_quality(link_text)
                        
                        full_link = response.urljoin(link_href)
                        self.logger.info(f'Extracting {server_name} link: {link_text}')
                        
                        self.driver.get(full_link)
                        time.sleep(5)
                        
                        final_url = self.driver.current_url
                        self.logger.info(f'Final URL: {final_url}')
                        
                        # Validate URL
                        invalid_patterns = ['goojara.to', '404', 'error', 'disable-devtool']
                        is_valid = (
                            final_url and 
                            len(final_url) > 20 and
                            not any(pattern in final_url.lower() for pattern in invalid_patterns)
                        )
                        
                        if is_valid:
                            all_streaming_links.append({
                                'url': final_url,
                                'server': server_name,
                                'quality': quality,
                                'language': 'EN'
                            })
                            self.logger.info(f'✓ Extracted {server_name} link: {final_url[:60]}...')
                        else:
                            self.logger.warning(f'Invalid {server_name} URL: {final_url}')
                        
                        # Return to movie page
                        self.driver.get(movie_page_url)
                        time.sleep(1)
                        
                    except Exception as e:
                        self.logger.warning(f'Failed to extract {server_name} link: {e}')
                        try:
                            self.driver.get(movie_page_url)
                            time.sleep(1)
                        except:
                            pass
            
            # Yield items for each streaming link
            if all_streaming_links:
                for stream_link in all_streaming_links:
                    item = MovieItem()
                    item['source_site'] = 'goojara.to'
                    item['source_url'] = response.url
                    item['imdb_id'] = imdb_id
                    item['title'] = title
                    item['year'] = year
                    item['synopsis'] = synopsis
                    item['poster_url'] = poster_url
                    item['stream_url'] = stream_link['url']
                    item['server_name'] = stream_link['server']
                    item['quality'] = stream_link['quality']
                    item['language'] = stream_link['language']
                    
                    self.logger.info(f'✓ {title} - {stream_link["server"]} ({stream_link["quality"]})')
                    yield item
            else:
                self.logger.warning(f'✗ No valid streaming links found for: {title}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

    def _extract_quality(self, link_text):
        """Extract quality from link text"""
        if not link_text:
            return 'SD'
        
        text_upper = link_text.upper()
        if 'HD' in text_upper or '1080' in text_upper:
            return 'HD'
        elif '720' in text_upper:
            return '720p'
        elif 'DVD' in text_upper:
            return 'DVD'
        else:
            return 'SD'
