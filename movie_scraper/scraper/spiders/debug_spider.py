# scraper/scraper/spiders/debug_spider.py
"""
Debug spider to inspect the actual HTML structure of target sites
"""
import scrapy
from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class DebugSpider(scrapy.Spider):
    name = 'debug'
    
    def __init__(self, url='https://makmoviestreaming.com/', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            self.driver = None

    def spider_closed(self, spider):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

    def parse(self, response):
        self.logger.info(f'=== DEBUGGING: {response.url} ===')
        
        # Regular Scrapy response
        self.logger.info(f'\n1. SCRAPY RESPONSE:')
        self.logger.info(f'   Status: {response.status}')
        self.logger.info(f'   Title: {response.css("title::text").get()}')
        self.logger.info(f'   Body length: {len(response.text)} chars')
        
        # Save regular HTML
        with open('debug_scrapy.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        self.logger.info('   Saved to: debug_scrapy.html')
        
        # Test selectors on regular response
        self.logger.info(f'\n2. TESTING SELECTORS (Scrapy):')
        selectors_to_test = [
            ('article', 'article'),
            ('article.item', 'article.item'),
            ('div.items', 'div.items'),
            ('movie links', 'a[href*="/movie/"]'),
            ('any links', 'a'),
        ]
        
        for name, selector in selectors_to_test:
            count = len(response.css(selector).getall())
            self.logger.info(f'   {name}: {count} found')
            if count > 0 and count < 5:
                samples = response.css(selector).getall()[:2]
                for i, sample in enumerate(samples):
                    self.logger.info(f'     Sample {i+1}: {sample[:100]}...')
        
        # Selenium response
        if self.driver:
            self.logger.info(f'\n3. SELENIUM RESPONSE:')
            self.driver.get(response.url)
            
            # Wait for content
            time.sleep(8)
            
            # Scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            selenium_html = self.driver.page_source
            
            # Save Selenium HTML
            with open('debug_selenium.html', 'w', encoding='utf-8') as f:
                f.write(selenium_html)
            self.logger.info('   Saved to: debug_selenium.html')
            self.logger.info(f'   Body length: {len(selenium_html)} chars')
            
            # Create Scrapy response from Selenium
            from scrapy.http import HtmlResponse
            sel_response = HtmlResponse(
                url=response.url,
                body=selenium_html.encode('utf-8'),
                encoding='utf-8'
            )
            
            self.logger.info(f'\n4. TESTING SELECTORS (Selenium):')
            for name, selector in selectors_to_test:
                count = len(sel_response.css(selector).getall())
                self.logger.info(f'   {name}: {count} found')
                if count > 0 and count < 5:
                    samples = sel_response.css(selector).getall()[:2]
                    for i, sample in enumerate(samples):
                        self.logger.info(f'     Sample {i+1}: {sample[:100]}...')
            
            # Find movie links
            self.logger.info(f'\n5. MOVIE LINKS ANALYSIS:')
            movie_link_selectors = [
                'article.item a::attr(href)',
                'div.items a::attr(href)',
                'a[href*="/movie/"]::attr(href)',
            ]
            
            for selector in movie_link_selectors:
                links = sel_response.css(selector).getall()
                self.logger.info(f'   {selector}: {len(links)} links')
                if links:
                    for link in links[:3]:
                        self.logger.info(f'     - {link}')
        
        self.logger.info('\n=== DEBUG COMPLETE ===')
        self.logger.info('Check debug_scrapy.html and debug_selenium.html files')