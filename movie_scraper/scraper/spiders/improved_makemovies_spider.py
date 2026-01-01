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
from selenium.common.exceptions import TimeoutException
from scraper.items import MovieItem
import time
import re
import json

class ImprovedMakemoviesSpider(scrapy.Spider):
    name = 'improved_makemovies'
    allowed_domains = ['worldfreemovies.xyz']
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
        self.logger.info('Initializing Selenium WebDriver...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.logger.info('✓ Selenium WebDriver initialized')

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def __init__(self, limit=20, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0

    def parse(self, response):
        self.logger.info(f'Loading page: {response.url}')
        
        try:
            self.driver.get(response.url)
            wait = WebDriverWait(self.driver, 20)
            
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.film_list-wrap')))
            except TimeoutException:
                self.logger.warning('Timeout waiting for content')
            
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            movie_links = sel_response.css('div.film_list-wrap div.flw-item a.film-poster::attr(href)').getall()
            if not movie_links:
                movie_links = sel_response.css('a[href*="/movie/"]::attr(href)').getall()
            
            self.logger.info(f'Found {len(movie_links)} movie links')
            
            for link in movie_links[:self.limit]:
                if self.count >= self.limit:
                    break
                    
                full_url = response.urljoin(link)
                self.count += 1
                self.logger.info(f'Queuing movie {self.count}: {full_url}')
                yield scrapy.Request(url=full_url, callback=self.parse_movie_page, dont_filter=True)
                
        except Exception as e:
            self.logger.error(f'Error parsing homepage: {e}')

    def parse_movie_page(self, response):
        self.logger.info(f'Parsing movie page: {response.url}')
        
        try:
            self.driver.get(response.url)
            wait = WebDriverWait(self.driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.heading-name')))
            except TimeoutException:
                pass
            
            time.sleep(5)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            
            item = MovieItem()
            item['source_site'] = '123movies.com'
            item['source_url'] = response.url
            
            # Title
            title = sel_response.css('h2.heading-name a::text').get()
            if not title:
                title = sel_response.css('h2.heading-name::text').get()
            item['title'] = title.strip() if title else 'Unknown Title'
            
            # IMDB ID
            url_match = re.search(r'/movie/([^/]+)-([^/]+)W/', response.url)
            if url_match:
                imdb_id = url_match.group(2)
            else:
                imdb_id = f'123m_{hash(response.url)}'
            item['imdb_id'] = f'123movies_{imdb_id}'
            
            # Year
            year = None
            year_text = sel_response.css('div.elements div.row-line:contains("Released:") *::text').getall()
            if year_text:
                year_str = ' '.join(year_text)
                year_match = re.search(r'(20\d{2}|19\d{2})', year_str)
                if year_match:
                    year = int(year_match.group(1))
            if not year:
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
            
            # Stream URL - Try multiple selectors to find server links
            # Try data-linkid first
            stream_links = sel_response.css('a[data-linkid]')
            
            # If not found, try other common selectors
            if not stream_links:
                stream_links = sel_response.css('ul.episodes a')
            if not stream_links:
                stream_links = sel_response.css('div.server a')
            if not stream_links:
                stream_links = sel_response.css('a.btn-server')
            
            # Debug: log all links found
            all_links = sel_response.css('a::attr(href)').getall()
            self.logger.info(f'Total links on page: {len(all_links)}')
            
            if stream_links:
                self.logger.info(f'Found {len(stream_links)} server links')
                
                # Try first link
                link_id = stream_links[0].css('::attr(data-linkid)').get()
                
                if link_id:
                    try:
                        ajax_url = f'https://worldfreemovies.xyz/ajax/episode/sources/{link_id}'
                        self.logger.info(f'Getting stream from: {ajax_url}')
                        
                        self.driver.get(ajax_url)
                        time.sleep(2)
                        
                        page_source = self.driver.page_source
                        
                        # Parse JSON response
                        try:
                            json_match = re.search(r'\{.*"link".*\}', page_source)
                            if json_match:
                                data = json.loads(json_match.group())
                                stream_url = data.get('link', '')
                            else:
                                stream_url = ''
                        except:
                            stream_url = ''
                        
                        if stream_url and 'http' in stream_url:
                            item['stream_url'] = stream_url
                            item['quality'] = 'HD'
                            item['language'] = 'EN'
                            self.logger.info(f'✓ Successfully extracted: {item["title"]}')
                            yield item
                        else:
                            self.logger.warning(f'✗ No valid stream URL')
                            item['stream_url'] = ''
                            item['quality'] = 'N/A'
                            item['language'] = 'EN'
                            yield item
                            
                    except Exception as e:
                        self.logger.error(f'Error extracting stream: {e}')
                        item['stream_url'] = ''
                        item['quality'] = 'N/A'
                        item['language'] = 'EN'
                        yield item
                else:
                    item['stream_url'] = ''
                    item['quality'] = 'N/A'
                    item['language'] = 'EN'
                    yield item
            else:
                self.logger.warning(f'✗ No streaming links found')
                item['stream_url'] = ''
                item['quality'] = 'N/A'
                item['language'] = 'EN'
                yield item
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
