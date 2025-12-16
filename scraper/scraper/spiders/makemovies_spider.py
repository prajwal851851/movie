# scraper/scraper/spiders/makemovies_spider.py
import scrapy
from scraper.items import MovieItem

class MakemoviesSpider(scrapy.Spider):
    name = 'makemovies'
    allowed_domains = ['makmoviestreaming.com']
    # We will start on the listing page
    start_urls = ['https://makmoviestreaming.com/movie/']

    def parse(self, response):
        # Find all movie links on the listing page
        movie_links = response.css('div.items > a::attr(href)').getall()
        for link in movie_links:
            yield response.follow(link, callback=self.parse_movie_page)

        # Follow pagination
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_movie_page(self, response):
        item = MovieItem()
        item['source_site'] = 'makmoviestreaming.com'
        item['source_url'] = response.url
        
        # Extract details using CSS selectors
        item['title'] = response.css('h1.entry-title::text').get().strip()
        item['imdb_id'] = response.url.split('/')[-1] # Use URL slug as ID
        item['year'] = response.css('span.year::text').get()
        item['synopsis'] = response.css('div#info > p:nth-child(2)::text').get()
        item['poster_url'] = response.css('div.poster > img::attr(src)').get()
        
        # This site uses an iframe, let's grab its src
        iframe_src = response.css('div.iframe-player iframe::attr(src)').get()
        if iframe_src:
            item['stream_url'] = iframe_src
            item['quality'] = 'HD' # Default quality
            item['language'] = 'EN'
            yield item