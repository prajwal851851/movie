# scraper/scraper/spiders/working_archive_spider.py
"""
Reliable spider for Archive.org movies - uses JSON API
"""
import scrapy
from scraper.items import MovieItem
import re
import json
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie

class WorkingArchiveSpider(scrapy.Spider):
    name = 'working_archive'
    allowed_domains = ['archive.org']
    
    # Use Archive.org's search API
    def start_requests(self):
        # Search for HD quality sci-fi movies, prioritizing recently added content
        # Note: Archive.org's year field is often the upload date, not movie release year
        collections = ['opensource_movies', 'feature_films', 'moviesandfilms']

        for collection in collections:
            # Search for HD format sci-fi movies, sorted by recently added
            # Note: Archive.org's year field is upload date, not movie release year
            url = (
                f'https://archive.org/advancedsearch.php?'
                f'q=collection:{collection}+AND+mediatype:movies'
                f'+AND+(format:h.264+OR+format:"MPEG4"+OR+format:"h.264+HD")'
                f'&fl[]=identifier&fl[]=title&fl[]=year&fl[]=description&fl[]=date&fl[]=subject'
                f'&sort[]=addeddate+desc&rows=200&page=1&output=json'
            )
            yield scrapy.Request(url, callback=self.parse_api_response, meta={'collection': collection})
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.count = 0
        self.year_counts = {}

    def parse_api_response(self, response):
        """Parse JSON API response"""
        collection = response.meta.get('collection', 'unknown')
        self.logger.info(f'Parsing API response for collection: {collection}')
        
        try:
            data = json.loads(response.text)
            docs = data.get('response', {}).get('docs', [])
            
            self.logger.info(f'Found {len(docs)} items in API response')
            
            for doc in docs:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                identifier = doc.get('identifier')
                if identifier:
                    # Get the detail page for metadata
                    movie_url = f'https://archive.org/details/{identifier}'
                    self.count += 1
                    yield scrapy.Request(
                        movie_url,
                        callback=self.parse_movie,
                        meta={'api_data': doc}
                    )
        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse JSON: {e}')

    def parse_movie(self, response):
        """Parse individual movie page"""
        self.logger.info(f'Parsing movie: {response.url}')
        
        api_data = response.meta.get('api_data', {})
        
        item = MovieItem()
        item['source_site'] = 'archive.org'
        item['source_url'] = response.url
        
        # Extract identifier from URL
        url_parts = response.url.split('/')
        url_id = url_parts[-1] if url_parts else None
        item['imdb_id'] = f'archive_{url_id}'

        # Check if movie already exists in database
        try:
            existing_movie = Movie.objects.filter(imdb_id=item['imdb_id']).first()
            if existing_movie:
                self.logger.info(f'⊘ Skipping already scraped movie: {existing_movie.title} (ID: {item["imdb_id"]})')
                return
        except Exception as e:
            self.logger.warning(f'Could not check database for duplicates: {e}')

        # Get title from API data or page
        title = api_data.get('title')
        if not title:
            title = response.css('h1[itemprop="name"]::text').get()
        if not title:
            title = response.xpath('//meta[@property="og:title"]/@content').get()

        item['title'] = title.strip() if title else 'Unknown'

        # Skip trailers
        if 'trailer' in title.lower():
            self.logger.info(f'⊘ Skipping trailer: {title}')
            return

        # Extract actual movie release year from title (not upload year)
        year = None
        
        # First try to extract year from title (most reliable for Archive.org)
        year_match = re.search(r'\((\d{4})\)', str(title))
        if year_match:
            year = int(year_match.group(1))
        elif re.search(r'\b(19|20)\d{2}\b', str(title)):
            # Try to find 4-digit year in title
            year_match = re.search(r'\b(19|20)\d{2}\b', str(title))
            if year_match:
                year = int(year_match.group(0))
        
        # Filter for latest available movies (2010-2024)
        if not year or not (2010 <= year <= 2025):
            self.logger.info(f'⊘ Skipping {title} - Year {year} not in 2010-2024 range')
            return

        # Collect year statistics
        if year:
            if year not in self.year_counts:
                self.year_counts[year] = 0
            self.year_counts[year] += 1
        
        item['year'] = year
        
        # Get description from API data or page
        desc = api_data.get('description')
        if not desc:
            desc = response.xpath('//meta[@property="og:description"]/@content').get()
        
        item['synopsis'] = desc.strip() if desc else ''
        
        # Extract poster/thumbnail
        poster = response.xpath('//meta[@property="og:image"]/@content').get()
        if not poster and url_id:
            # Archive.org has predictable thumbnail URLs
            poster = f'https://archive.org/services/img/{url_id}'
        
        item['poster_url'] = poster if poster else ''
        
        # Get video URL using Archive.org's metadata API
        if url_id:
            # Request the metadata JSON to get actual file information
            metadata_url = f'https://archive.org/metadata/{url_id}'
            yield scrapy.Request(
                metadata_url,
                callback=self.parse_metadata,
                meta={'item': item, 'url_id': url_id}
            )
        else:
            self.logger.warning(f'✗ No identifier found for: {item["title"]}')
    
    def parse_metadata(self, response):
        """Parse metadata JSON to get HD quality video file URLs (720p-1080p)"""
        item = response.meta['item']
        url_id = response.meta['url_id']
        
        try:
            metadata = json.loads(response.text)
            files = metadata.get('files', [])
            
            # Find video files and prioritize HD quality (720p-1080p)
            video_files = []
            for file_info in files:
                name = file_info.get('name', '')
                format_type = file_info.get('format', '').lower()
                height = file_info.get('height', 0)
                width = file_info.get('width', 0)
                size = file_info.get('size', 0)
                
                # Look for MP4/MPEG4 video formats
                if any(ext in name.lower() for ext in ['.mp4', '.mpeg']):
                    is_hd = False
                    quality_label = 'SD'
                    priority = 3  # Lower number = higher priority
                    
                    # Check by resolution (highest priority)
                    if height and width:
                        height_int = int(height)
                        if 720 <= height_int <= 1080:
                            is_hd = True
                            quality_label = f'{height_int}p'
                            priority = 1 if height_int >= 1080 else 2
                    
                    # Check by filename indicators
                    name_lower = name.lower()
                    if any(indicator in name_lower for indicator in ['1080p', '1080']):
                        is_hd = True
                        quality_label = '1080p'
                        priority = 1
                    elif any(indicator in name_lower for indicator in ['720p', '720']):
                        is_hd = True
                        quality_label = '720p'
                        priority = 2
                    elif 'hd' in name_lower and not is_hd:
                        quality_label = 'HD'
                        priority = 2
                    
                    # Check by file size (good quality indicator)
                    size_int = int(size) if size else 0
                    if size_int > 700000000:  # > 700MB likely HD
                        if not is_hd:
                            quality_label = 'HD'
                            priority = 2
                    
                    video_files.append({
                        'name': name,
                        'format': format_type,
                        'size': size_int,
                        'quality': quality_label,
                        'height': int(height) if height else 0,
                        'priority': priority,
                        'is_hd': is_hd
                    })
            
            # Sort: HD first, then by priority (1080p > 720p), then by size
            video_files.sort(key=lambda x: (
                0 if x['is_hd'] else 1,  # HD files first
                x['priority'],             # 1080p > 720p > others
                -x['size']                 # Larger files first
            ))
            
            if video_files:
                best_file = video_files[0]
                stream_url = f'https://archive.org/download/{url_id}/{best_file["name"]}'
                
                item['stream_url'] = stream_url
                item['quality'] = best_file['quality']
                item['language'] = 'EN'
                
                if best_file['is_hd']:
                    self.logger.info(f'✓ Successfully extracted HD: {item["title"]} ({best_file["quality"]}) - {best_file["name"]}')
                else:
                    self.logger.info(f'✓ Successfully extracted: {item["title"]} ({best_file["quality"]}) - {best_file["name"]}')
                yield item
            else:
                # No video files found
                self.logger.warning(f'✗ No video files found for: {item["title"]} - Skipping')
                
        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse metadata JSON: {e}')
        except Exception as e:
            self.logger.error(f'Error processing metadata for {item["title"]}: {e}')

    def closed(self, reason):
        """Print year statistics when spider closes"""
        self.logger.info("=== MOVIE YEAR STATISTICS ===")
        if self.year_counts:
            sorted_years = sorted(self.year_counts.items(), key=lambda x: x[0])
            for year, count in sorted_years:
                self.logger.info(f"Year {year}: {count} movies")
        else:
            self.logger.info("No year data collected")
        self.logger.info("=== END STATISTICS ===")
