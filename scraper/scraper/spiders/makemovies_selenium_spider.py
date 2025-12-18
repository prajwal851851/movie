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
from selenium.common.exceptions import TimeoutException, WebDriverException
from scraper.items import MovieItem
import time
import logging

class MakemoviesSeleniumSpider(scrapy.Spider):
    name = 'selenium_movies'
    allowed_domains = ['makmoviestreaming.com']
    start_urls = ['https://makmoviestreaming.com/movie/']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,  # Selenium doesn't handle concurrent well
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium WebDriver with proper options"""
        self.logger.info('Setting up Selenium WebDriver...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            # Execute script to hide webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            self.logger.info('✓ Selenium WebDriver ready')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        """Clean up Selenium"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def parse(self, response):
        """Parse listing page with Selenium"""
        self.logger.info(f'Loading page: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            # Wait for content - try multiple selectors
            wait = WebDriverWait(self.driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article.item')))
            except TimeoutException:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.items')))
                except TimeoutException:
                    self.logger.warning('Page content did not load in time')
                    return
            
            # Extra wait for JavaScript
            time.sleep(5)
            
            # Scroll to load lazy images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url, 
                body=html.encode('utf-8'), 
                encoding='utf-8'
            )
            
            # Find movie links with multiple selectors
            movie_links = []
            
            # Try different patterns
            selectors = [
                'article.item div.poster a::attr(href)',
                'div.items article a::attr(href)',
                'a[href*="/movie/"]::attr(href)',
            ]
            
            for selector in selectors:
                links = sel_response.css(selector).getall()
                if links:
                    movie_links = links
                    self.logger.info(f'Found {len(links)} links with: {selector}')
                    break
            
            if not movie_links:
                self.logger.warning('No movie links found!')
                # Save debug HTML
                with open('debug_selenium.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.info('Saved debug HTML to debug_selenium.html')
                return
            
            # Get unique links
            unique_links = list(set([link for link in movie_links if '/movie/' in link]))
            self.logger.info(f'Processing {len(unique_links)} unique movie links')
            
            # Limit to avoid too many requests
            for link in unique_links[:10]:
                yield scrapy.Request(url=link, callback=self.parse_movie_page)
            
        except WebDriverException as e:
            self.logger.error(f'Selenium error: {e}')
        except Exception as e:
            self.logger.error(f'Error parsing page: {e}')

    def parse_movie_page(self, response):
        """Parse individual movie page"""
        self.logger.info(f'Loading movie: {response.url}')
        
        try:
            self.driver.get(response.url)
            
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
            time.sleep(3)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            item = MovieItem()
            item['source_site'] = 'makmoviestreaming.com'
            item['source_url'] = response.url
            
            # Extract with multiple fallbacks
            title = (
                sel_response.css('h1.entry-title::text').get() or
                sel_response.css('h1::text').get() or
                sel_response.css('div.data h1::text').get()
            )
            item['title'] = title.strip() if title else 'Unknown'
            
            # Extract ID
            url_parts = response.url.rstrip('/').split('/')
            item['imdb_id'] = url_parts[-1] if url_parts else f'makm_{hash(response.url)}'
            
            # Year
            year = (
                sel_response.css('span.year::text').get() or
                sel_response.css('span.date::text').get()
            )
            if year:
                import re
                year_match = re.search(r'(\d{4})', year)
                item['year'] = int(year_match.group(1)) if year_match else None
            else:
                item['year'] = None
            
            # Synopsis
            synopsis = (
                sel_response.css('div.wp-content p::text').get() or
                sel_response.css('div[itemprop="description"]::text').get() or
                sel_response.css('div.description::text').get()
            )
            item['synopsis'] = synopsis.strip() if synopsis else ''
            
            # Poster
            poster = (
                sel_response.css('div.poster img::attr(src)').get() or
                sel_response.css('img.wp-post-image::attr(src)').get() or
                sel_response.css('meta[property="og:image"]::attr(content)').get()
            )
            item['poster_url'] = poster or ''
            
            # Stream URL - try to find iframe
            iframe_selectors = [
                'div.player iframe::attr(src)',
                'iframe[src*="embed"]::attr(src)',
                'iframe::attr(src)',
            ]
            
            stream_url = None
            for selector in iframe_selectors:
                stream_url = sel_response.css(selector).get()
                if stream_url:
                    break
            
            if stream_url:
                item['stream_url'] = stream_url
                item['quality'] = 'HD'
                item['language'] = 'EN'
                self.logger.info(f'✓ Extracted: {item["title"]}')
                yield item
            else:
                self.logger.warning(f'✗ No stream for: {item["title"]}')
                
        except Exception as e:
            self.logger.error(f'Error parsing movie {response.url}: {e}')
