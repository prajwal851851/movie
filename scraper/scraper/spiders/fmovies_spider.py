# scraper/scraper/spiders/fmovies_spider.py
import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from scraper.items import MovieItem
import time
import re
from urllib.parse import urlparse

class FmoviesSpider(scrapy.Spider):
    name = 'fmovies'
    allowed_domains = ['fmovies-co.net', 'makmoviestreaming.com']
    start_urls = ['https://makmoviestreaming.com/movie/']

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': False,
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FmoviesSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)

    def spider_closed(self, spider):
        self.driver.quit()

    def parse(self, response):
        self.logger.info(f'Loading page with Selenium: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            # Wait for content to load
            wait = WebDriverWait(self.driver, 15)
            # Try multiple possible selectors
            wait.until(lambda d: 
                d.find_elements(By.CSS_SELECTOR, 'article.item') or
                d.find_elements(By.CSS_SELECTOR, 'div.film_list-wrap') or
                d.find_elements(By.CSS_SELECTOR, 'div.flw-item')
            )
            
            time.sleep(3)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            # Multiple selector patterns for movie links
            movie_selectors = [
                'article.item a::attr(href)',
                'div.flw-item a::attr(href)',
                'div.film_list-wrap a::attr(href)',
                'a.film-poster-ahref::attr(href)',
                'div.movie-item a::attr(href)',
                'a[href*="/movie/"]::attr(href)',
            ]
            
            movie_links = []
            for selector in movie_selectors:
                links = sel_response.css(selector).getall()
                if links:
                    self.logger.info(f'Found {len(links)} links with selector: {selector}')
                    movie_links = links
                    break
            
            unique_links = set()
            for link in movie_links[:20]:  # Limit to 20 movies per page
                if '/movie/' in link and link not in unique_links:
                    unique_links.add(link)
                    full_url = response.urljoin(link)
                    yield scrapy.Request(url=full_url, callback=self.parse_movie_page)
            
            # Pagination
            current_page = getattr(self, 'page_count', 1)
            if current_page < 3:
                next_selectors = [
                    'a.next::attr(href)',
                    'a[rel="next"]::attr(href)',
                    'li.next a::attr(href)',
                    'a.pagination-next::attr(href)',
                ]
                for selector in next_selectors:
                    next_link = sel_response.css(selector).get()
                    if next_link:
                        self.page_count = current_page + 1
                        full_url = response.urljoin(next_link)
                        yield scrapy.Request(url=full_url, callback=self.parse)
                        break
                    
        except TimeoutException:
            self.logger.error(f'Timeout loading page: {response.url}')
        except Exception as e:
            self.logger.error(f'Error parsing page: {str(e)}')

    def parse_movie_page(self, response):
        self.logger.info(f'Loading movie page: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
            
            # Wait for video player to load
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            item = MovieItem()
            item['source_site'] = urlparse(response.url).netloc
            item['source_url'] = response.url
            
            # Extract title
            title_selectors = [
                'h1.heading-name a::text',
                'h1.film-name::text',
                'h1.entry-title::text',
                'h1::text',
                'meta[property="og:title"]::attr(content)',
            ]
            title = None
            for selector in title_selectors:
                title = sel_response.css(selector).get()
                if title:
                    break
            item['title'] = title.strip() if title else 'Unknown'
            
            # Extract IMDB ID from URL or data attribute
            url_parts = response.url.rstrip('/').split('/')
            imdb_id = url_parts[-1] if url_parts else None
            
            # Try to find IMDB ID in the page
            if not imdb_id or len(imdb_id) < 5:
                imdb_link = sel_response.css('a[href*="imdb.com"]::attr(href)').get()
                if imdb_link:
                    imdb_match = re.search(r'(tt\d+)', imdb_link)
                    if imdb_match:
                        imdb_id = imdb_match.group(1)
            
            item['imdb_id'] = imdb_id or f'fm_{hash(response.url)}'
            
            # Extract year
            year_selectors = [
                'span.year::text',
                'span.fdi-item:contains("Released")::text',
                'div.film-infor span:nth-child(1)::text',
            ]
            year = None
            for selector in year_selectors:
                year_text = sel_response.css(selector).get()
                if year_text:
                    year_match = re.search(r'20\d{2}|19\d{2}', year_text)
                    if year_match:
                        year = year_match.group()
                        break
            item['year'] = year
            
            # Extract synopsis
            synopsis_selectors = [
                'div.description::text',
                'div.film-description::text',
                'div.desc::text',
                'p.description::text',
                'meta[property="og:description"]::attr(content)',
            ]
            synopsis = None
            for selector in synopsis_selectors:
                synopsis = sel_response.css(selector).get()
                if synopsis:
                    break
            item['synopsis'] = synopsis.strip() if synopsis else ''
            
            # Extract poster
            poster_selectors = [
                'img.film-poster-img::attr(src)',
                'div.film-poster img::attr(src)',
                'div.poster img::attr(src)',
                'meta[property="og:image"]::attr(content)',
            ]
            poster = None
            for selector in poster_selectors:
                poster = sel_response.css(selector).get()
                if poster:
                    break
            item['poster_url'] = poster or ''
            
            # Extract streaming URL
            iframe_selectors = [
                'iframe#iframe-embed::attr(src)',
                'iframe[src*="embed"]::attr(src)',
                'iframe[data-src*="embed"]::attr(data-src)',
                'div#iframe-embed iframe::attr(src)',
                'div.watch-player iframe::attr(src)',
            ]
            
            stream_url = None
            for selector in iframe_selectors:
                stream_url = sel_response.css(selector).get()
                if stream_url:
                    self.logger.info(f'Found stream URL with selector: {selector}')
                    break
            
            # Check for data-src attributes
            if not stream_url:
                iframe_data = sel_response.css('iframe::attr(data-src)').get()
                if iframe_data:
                    stream_url = iframe_data
            
            # Also check for video elements
            if not stream_url:
                video_selectors = [
                    'video source::attr(src)',
                    'video::attr(src)',
                ]
                for selector in video_selectors:
                    stream_url = sel_response.css(selector).get()
                    if stream_url:
                        break
            
            if stream_url:
                item['stream_url'] = stream_url
                item['quality'] = 'HD'
                item['language'] = 'EN'
                self.logger.info(f'Successfully extracted: {item["title"]}')
                yield item
            else:
                self.logger.warning(f'No stream URL found for: {item["title"]}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page {response.url}: {str(e)}')