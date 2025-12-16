# scraper/scraper/spiders/makemovies_selenium_spider.py
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

class MakemoviesSeleniumSpider(scrapy.Spider):
    name = 'makemovies_selenium'
    allowed_domains = ['makmoviestreaming.com']
    start_urls = ['https://makmoviestreaming.com/movie/']

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MakemoviesSeleniumSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        # Setup Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
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
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article.item')))
            
            # Give extra time for all content to load
            time.sleep(3)
            
            # Get the rendered HTML
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            # Find movie links
            movie_links = sel_response.css('article.item a::attr(href)').getall()
            self.logger.info(f'Found {len(movie_links)} movie links')
            
            # Get unique movie page links
            unique_links = set()
            for link in movie_links:
                if '/movie/' in link and link not in unique_links:
                    unique_links.add(link)
                    yield scrapy.Request(url=link, callback=self.parse_movie_page)
            
            # Handle pagination - limit to first 3 pages for testing
            current_page = getattr(self, 'page_count', 1)
            if current_page < 3:
                next_link = sel_response.css('a.next.page-numbers::attr(href)').get()
                if next_link:
                    self.page_count = current_page + 1
                    yield scrapy.Request(url=next_link, callback=self.parse)
                    
        except TimeoutException:
            self.logger.error(f'Timeout loading page: {response.url}')
        except Exception as e:
            self.logger.error(f'Error parsing page: {str(e)}')

    def parse_movie_page(self, response):
        self.logger.info(f'Loading movie page: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            # Wait for movie content
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
            time.sleep(2)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            item = MovieItem()
            item['source_site'] = 'makmoviestreaming.com'
            item['source_url'] = response.url
            
            # Extract title
            title = sel_response.css('h1::text').get()
            item['title'] = title.strip() if title else 'Unknown'
            
            # Extract IMDB ID from URL
            url_parts = response.url.rstrip('/').split('/')
            imdb_id = url_parts[-1] if url_parts else f'movie_{hash(response.url)}'
            item['imdb_id'] = imdb_id
            
            # Extract year
            year_text = sel_response.css('span.year::text, span.date::text').get()
            item['year'] = year_text.strip() if year_text else None
            
            # Extract synopsis
            synopsis = sel_response.css('div.wp-content p::text, div[itemprop="description"]::text').get()
            item['synopsis'] = synopsis.strip() if synopsis else ''
            
            # Extract poster
            poster = (
                sel_response.css('div.poster img::attr(src)').get() or
                sel_response.css('meta[property="og:image"]::attr(content)').get()
            )
            item['poster_url'] = poster or ''
            
            # Extract streaming URL
            iframe_src = sel_response.css('iframe::attr(src)').get()
            
            if iframe_src:
                item['stream_url'] = iframe_src
                item['quality'] = 'HD'
                item['language'] = 'EN'
                self.logger.info(f'Successfully extracted: {item["title"]}')
                yield item
            else:
                self.logger.warning(f'No stream URL found for: {item["title"]}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page {response.url}: {str(e)}')