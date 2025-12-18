import scrapy
from scraper.items import MovieItem
import re

class ImprovedArchiveSpider(scrapy.Spider):
    name = 'archive_movies'
    allowed_domains = ['archive.org']
    
    # Multiple collections for variety
    start_urls = [
        'https://archive.org/details/feature_films',
        'https://archive.org/details/classic_tv',
        'https://archive.org/details/moviesandfilms',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, limit=30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0

    def parse(self, response):
        self.logger.info(f'Parsing collection: {response.url}')
        
        # Find all movie items
        movie_links = response.css('div.item-ia a.stealth::attr(href)').getall()
        
        for link in movie_links:
            if self.count >= self.limit:
                self.logger.info(f'Reached limit of {self.limit} movies')
                return
                
            movie_url = response.urljoin(link)
            self.count += 1
            yield scrapy.Request(movie_url, callback=self.parse_movie)

    def parse_movie(self, response):
        self.logger.info(f'Parsing movie: {response.url}')
        
        item = MovieItem()
        item['source_site'] = 'archive.org'
        item['source_url'] = response.url
        
        # Extract title
        title = response.css('h1[itemprop="name"]::text').get()
        if not title:
            title = response.css('h1::text').get()
        item['title'] = title.strip() if title else 'Unknown'
        
        # Create ID from URL
        url_id = response.url.split('/')[-1]
        item['imdb_id'] = f'archive_{url_id}'
        
        # Extract year
        date_text = response.css('div.metadata-definition:-soup-contains("Date") + div::text').get()
        if date_text:
            year_match = re.search(r'(\d{4})', date_text)
            item['year'] = int(year_match.group(1)) if year_match else None
        else:
            item['year'] = None
        
        # Extract description
        desc = response.css('div[itemprop="description"]::text').get()
        if not desc:
            desc = response.css('div.description::text').get()
        item['synopsis'] = desc.strip() if desc else ''
        
        # Extract poster
        poster = response.css('img[itemprop="image"]::attr(src)').get()
        if not poster:
            poster = response.css('img.img-fluid::attr(src)').get()
        item['poster_url'] = response.urljoin(poster) if poster else ''
        
        # Get video URL - try multiple formats
        video_sources = response.css('video source::attr(src)').getall()
        
        # Prefer MP4 format
        mp4_sources = [src for src in video_sources if '.mp4' in src.lower()]
        
        if mp4_sources:
            item['stream_url'] = response.urljoin(mp4_sources[0])
            item['quality'] = 'SD'
            item['language'] = 'EN'
            self.logger.info(f'✓ Successfully extracted: {item["title"]}')
            yield item
        else:
            self.logger.warning(f'✗ No video found for: {item["title"]}')
