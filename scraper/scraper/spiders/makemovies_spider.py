# scraper/scraper/spiders/makemovies_spider.py
import scrapy
from scraper.items import MovieItem

class MakemoviesSpider(scrapy.Spider):
    name = 'makemovies'
    allowed_domains = ['makmoviestreaming.com']
    start_urls = ['https://makmoviestreaming.com/movie/']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def parse(self, response):
        self.logger.info(f'Parsing listing page: {response.url}')
        self.logger.info(f'Response status: {response.status}')
        
        # Try multiple selector patterns
        selectors = [
            'div.items > a::attr(href)',
            'article a::attr(href)',
            'div.poster a::attr(href)',
            'a[href*="/movie/"]::attr(href)',
        ]
        
        movie_links = []
        for selector in selectors:
            links = response.css(selector).getall()
            if links:
                self.logger.info(f'Found {len(links)} links with selector: {selector}')
                movie_links = links
                break
        
        if not movie_links:
            self.logger.warning('No movie links found! Trying XPath...')
            movie_links = response.xpath('//article//a/@href').getall()
            self.logger.info(f'XPath found {len(movie_links)} links')
        
        # Process movie links
        for link in movie_links:
            if link and '/movie/' in link:
                self.logger.info(f'Following movie link: {link}')
                yield response.follow(link, callback=self.parse_movie_page)
        
        # Follow pagination
        next_selectors = [
            'a.next.page-numbers::attr(href)',
            'a[rel="next"]::attr(href)',
            'div.pagination a:contains("Next")::attr(href)',
        ]
        
        for selector in next_selectors:
            next_page = response.css(selector).get()
            if next_page:
                self.logger.info(f'Following pagination: {next_page}')
                yield response.follow(next_page, callback=self.parse)
                break

    def parse_movie_page(self, response):
        self.logger.info(f'Parsing movie page: {response.url}')
        
        item = MovieItem()
        item['source_site'] = 'makmoviestreaming.com'
        item['source_url'] = response.url
        
        # Extract title with multiple fallbacks
        title = (
            response.css('h1.entry-title::text').get() or
            response.css('h1::text').get() or
            response.css('div.data h1::text').get() or
            ''
        )
        item['title'] = title.strip() if title else 'Unknown'
        
        # Extract IMDB ID from URL or meta
        imdb_id = response.url.split('/')[-2] if response.url.endswith('/') else response.url.split('/')[-1]
        item['imdb_id'] = imdb_id or f'unknown_{hash(response.url)}'
        
        # Extract year
        year = (
            response.css('span.year::text').get() or
            response.css('span.date::text').get() or
            response.xpath('//span[contains(@class, "year")]/text()').get()
        )
        item['year'] = year.strip() if year else None
        
        # Extract synopsis
        synopsis = (
            response.css('div#info > p:nth-child(2)::text').get() or
            response.css('div.wp-content p::text').get() or
            response.css('div[itemprop="description"]::text').get() or
            ''
        )
        item['synopsis'] = synopsis.strip() if synopsis else ''
        
        # Extract poster
        poster = (
            response.css('div.poster > img::attr(src)').get() or
            response.css('img.wp-post-image::attr(src)').get() or
            response.css('meta[property="og:image"]::attr(content)').get()
        )
        item['poster_url'] = poster or ''
        
        # Extract streaming URL
        iframe_selectors = [
            'div.iframe-player iframe::attr(src)',
            'div.player iframe::attr(src)',
            'iframe[src*="embed"]::attr(src)',
            'iframe::attr(src)',
        ]
        
        stream_url = None
        for selector in iframe_selectors:
            stream_url = response.css(selector).get()
            if stream_url:
                self.logger.info(f'Found stream URL with selector: {selector}')
                break
        
        if stream_url:
            item['stream_url'] = stream_url
            item['quality'] = 'HD'
            item['language'] = 'EN'
            self.logger.info(f'Successfully extracted movie: {item["title"]}')
            yield item
        else:
            self.logger.warning(f'No stream URL found for: {item["title"]} at {response.url}')