# scraper/scraper/spiders/test_spider.py
import scrapy

class TestSpider(scrapy.Spider):
    name = 'test'
    
    def __init__(self, url=None, *args, **kwargs):
        super(TestSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else ['https://makmoviestreaming.com/movie/']
    
    def parse(self, response):
        # Save the HTML to a file for inspection
        filename = 'debug_page.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        
        self.logger.info(f'Saved page to {filename}')
        self.logger.info(f'Status code: {response.status}')
        self.logger.info(f'Page title: {response.css("title::text").get()}')
        
        # Try to find any links
        all_links = response.css('a::attr(href)').getall()
        self.logger.info(f'Found {len(all_links)} total links')
        
        # Look for movie-related divs or sections
        divs_with_items = response.css('div.items').getall()
        self.logger.info(f'Found {len(divs_with_items)} div.items elements')
        
        # Check for different common movie listing patterns
        patterns = [
            'div.items > a',
            'article a',
            'div.movie-item a',
            'div.poster a',
            'a.movie-link',
        ]
        
        for pattern in patterns:
            found = response.css(f'{pattern}::attr(href)').getall()
            if found:
                self.logger.info(f'Pattern "{pattern}" found {len(found)} matches')
                for link in found[:3]:  # Show first 3
                    self.logger.info(f'  - {link}')