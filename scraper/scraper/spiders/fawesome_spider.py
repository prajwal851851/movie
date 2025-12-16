# scraper/scraper/spiders/fawesome_spider.py
import scrapy
from scraper.items import MovieItem

class FawesomeSpider(scrapy.Spider):
    name = 'fawesome'
    allowed_domains = ['fawesome.tv']
    start_urls = ['https://fawesome.tv/movies']

    def parse(self, response):
        # Find all movie links
        movie_links = response.css('a.tile-link::attr(href)').getall()
        for link in movie_links:
            yield response.follow(link, callback=self.parse_movie_page)
        
        # Follow pagination (if it exists)
        next_page = response.css('a[aria-label="Next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_movie_page(self, response):
        item = MovieItem()
        item['source_site'] = 'fawesome.tv'
        item['source_url'] = response.url

        # Extract details
        item['title'] = response.css('h1.movie-title::text').get().strip()
        item['imdb_id'] = response.url.split('/')[-1]
        item['year'] = response.css('span.movie-year::text').get()
        item['synopsis'] = response.css('p.movie-description::text').get()
        item['poster_url'] = response.css('div.movie-poster img::attr(src)').get()
        
        # This site also uses an iframe
        iframe_src = response.css('div.video-player iframe::attr(src)').get()
        if iframe_src:
            item['stream_url'] = iframe_src
            item['quality'] = 'HD'
            item['language'] = 'EN'
            yield item