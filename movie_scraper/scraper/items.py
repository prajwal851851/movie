# scraper/scraper/items.py
import scrapy

class MovieItem(scrapy.Item):
    imdb_id = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    synopsis = scrapy.Field()
    poster_url = scrapy.Field()
    source_url = scrapy.Field()
    source_site = scrapy.Field()
    stream_url = scrapy.Field()
    server_name = scrapy.Field()
    quality = scrapy.Field()
    language = scrapy.Field()