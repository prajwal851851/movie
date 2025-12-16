# scraper/scraper/spiders/simple_movie_spider.py
"""
Since the target sites use JavaScript, this spider scrapes from 
a different free movie site that works with regular Scrapy.
"""
import scrapy
from scraper.items import MovieItem
import re

class SimpleMovieSpider(scrapy.Spider):
    name = 'simple_movies'
    allowed_domains = ['archive.org']
    start_urls = ['https://archive.org/details/movies']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def parse(self, response):
        self.logger.info(f'Parsing: {response.url}')
        
        # Find movie items
        movies = response.css('div.item-ia::attr(href)').getall()
        
        for movie_path in movies[:10]:  # Limit to 10 for testing
            movie_url = response.urljoin(movie_path)
            yield scrapy.Request(movie_url, callback=self.parse_movie)

    def parse_movie(self, response):
        self.logger.info(f'Parsing movie: {response.url}')
        
        item = MovieItem()
        item['source_site'] = 'archive.org'
        item['source_url'] = response.url
        
        # Extract title
        title = response.css('h1.item-title::text').get()
        item['title'] = title.strip() if title else 'Unknown'
        
        # Create a simple ID
        item['imdb_id'] = response.url.split('/')[-1] or f'archive_{hash(response.url)}'
        
        # Extract year from metadata
        year_text = response.css('span.metadata-definition:contains("Year")::text').get()
        if year_text:
            year_match = re.search(r'\d{4}', year_text)
            item['year'] = year_match.group() if year_match else None
        else:
            item['year'] = None
        
        # Extract description
        desc = response.css('div.item-description::text').get()
        item['synopsis'] = desc.strip() if desc else ''
        
        # Extract poster/thumbnail
        poster = response.css('img.item-image::attr(src)').get()
        item['poster_url'] = poster or ''
        
        # Get video URL
        video_url = response.css('video source::attr(src)').get()
        if video_url:
            item['stream_url'] = response.urljoin(video_url)
            item['quality'] = 'SD'
            item['language'] = 'EN'
            yield item
        else:
            self.logger.warning(f'No video found for {item["title"]}')