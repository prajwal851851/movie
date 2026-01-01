
# scraper/items.py
import scrapy

class MovieItem(scrapy.Item):
    # Movie metadata
    imdb_id = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    synopsis = scrapy.Field()
    poster_url = scrapy.Field()
    
    # Source information
    source_url = scrapy.Field()
    source_site = scrapy.Field()
    
    # Streaming link information
    stream_url = scrapy.Field()
    server_name = scrapy.Field()  # Server name (UpCloud, MegaCloud, VidCloud, etc.)
    quality = scrapy.Field()
    language = scrapy.Field()
    
    # TV Series support
    content_type = scrapy.Field()
    metadata = scrapy.Field()