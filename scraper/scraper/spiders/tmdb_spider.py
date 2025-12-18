import scrapy
from scraper.items import MovieItem
import os

class TMDBSpider(scrapy.Spider):
    name = 'tmdb_movies'
    allowed_domains = ['api.themoviedb.org', 'image.tmdb.org']
    
    # Get free API key from: https://www.themoviedb.org/settings/api
    API_KEY = os.environ.get('TMDB_API_KEY', 'YOUR_API_KEY_HERE')
    
    def __init__(self, pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.API_KEY or self.API_KEY == 'YOUR_API_KEY_HERE':
            raise scrapy.exceptions.CloseSpider('TMDB_API_KEY is missing. Set environment variable TMDB_API_KEY.')
        self.pages = int(pages)
        
        # Start URLs - popular movies
        self.start_urls = [
            f'https://api.themoviedb.org/3/movie/popular?api_key={self.API_KEY}&page={i}'
            for i in range(1, self.pages + 1)
        ]

    def parse(self, response):
        data = response.json()
        movies = data.get('results', [])
        
        self.logger.info(f'Found {len(movies)} movies on this page')
        
        for movie in movies:
            # Get detailed info for each movie
            movie_id = movie['id']
            detail_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.API_KEY}&append_to_response=videos'
            yield scrapy.Request(detail_url, callback=self.parse_movie_detail)

    def parse_movie_detail(self, response):
        movie = response.json()
        
        item = MovieItem()
        item['source_site'] = 'tmdb'
        item['source_url'] = f'https://www.themoviedb.org/movie/{movie["id"]}'
        
        # Use TMDB ID as IMDB ID placeholder (or fetch real IMDB ID)
        item['imdb_id'] = movie.get('imdb_id') or f'tmdb_{movie["id"]}'
        item['title'] = movie['title']
        
        # Extract year from release_date
        release_date = movie.get('release_date', '')
        item['year'] = int(release_date[:4]) if release_date else None
        
        item['synopsis'] = movie.get('overview', '')
        
        # Poster URL
        poster_path = movie.get('poster_path')
        if poster_path:
            item['poster_url'] = f'https://image.tmdb.org/t/p/w500{poster_path}'
        else:
            item['poster_url'] = ''
        
        # Get trailer/video URL
        videos = movie.get('videos', {}).get('results', [])
        youtube_videos = [v for v in videos if v['site'] == 'YouTube']
        
        if youtube_videos:
            # Use YouTube embed URL
            youtube_key = youtube_videos[0]['key']
            item['stream_url'] = f'https://www.youtube.com/embed/{youtube_key}'
            item['quality'] = 'HD'
            item['language'] = movie.get('original_language', 'EN').upper()
            
            self.logger.info(f'✓ Extracted: {item["title"]} ({item["year"]})')
            yield item
        else:
            self.logger.info(f'⚠ No video for: {item["title"]} (will still save movie info)')
            # Save movie even without video - you can add links later
            item['stream_url'] = ''
            item['quality'] = 'N/A'
            item['language'] = movie.get('original_language', 'EN').upper()
            yield item

        watch_item = MovieItem()
        watch_item['source_site'] = 'tmdb'
        watch_item['source_url'] = item['source_url']
        watch_item['imdb_id'] = item['imdb_id']
        watch_item['title'] = item['title']
        watch_item['year'] = item['year']
        watch_item['synopsis'] = item['synopsis']
        watch_item['poster_url'] = item['poster_url']
        watch_item['stream_url'] = f'https://www.themoviedb.org/movie/{movie["id"]}/watch'
        watch_item['quality'] = 'Where to watch'
        watch_item['language'] = item['language']
        yield watch_item
