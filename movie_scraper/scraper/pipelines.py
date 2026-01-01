# scraper/scraper/pipelines.py
from itemadapter import ItemAdapter
from streaming.models import Movie, StreamingLink
from twisted.internet import threads
import time
import logging

logger = logging.getLogger(__name__)

class DjangoItemPipeline:
    """
    Fixed pipeline with retry logic to handle SQLite database locking.
    """
    
    def __init__(self):
        self.max_retries = 5
        self.retry_delay = 0.5  # Start with 500ms delay
    
    def process_item(self, item, spider):
        # Use Twisted's deferToThread to run Django ORM in a separate thread
        return threads.deferToThread(self._process_item_sync, item, spider)

    def _process_item_sync(self, item, spider):
        """
        Synchronous processing of item in a separate thread with retry logic for database locks.
        """
        adapter = ItemAdapter(item)
        
        # Retry logic for database operations
        for attempt in range(self.max_retries):
            try:
                return self._save_item_to_db(adapter, spider)
            except Exception as e:
                error_message = str(e).lower()
                
                # Check if it's a database locked error
                if 'database is locked' in error_message:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        wait_time = self.retry_delay * (2 ** attempt)
                        spider.logger.warning(
                            f'Database locked (attempt {attempt + 1}/{self.max_retries}). '
                            f'Retrying in {wait_time}s... Item: {adapter.get("title")}'
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        spider.logger.error(
                            f'Failed to save item after {self.max_retries} attempts due to database lock: '
                            f'{adapter.get("title")} - {adapter.get("stream_url")}'
                        )
                        # Log the item for manual recovery
                        self._log_failed_item(adapter, spider)
                        raise
                else:
                    # Different error, log and raise
                    spider.logger.error(f'Error processing item: {e}')
                    raise
        
        return item

    def _save_item_to_db(self, adapter, spider):
        """
        Actually save the item to database.
        """
        # Create or update the Movie
        movie_defaults = {
            'title': adapter.get('title'),
            'year': adapter.get('year'),
            'synopsis': adapter.get('synopsis', ''),
            'poster_url': adapter.get('poster_url', ''),
            'source_url': adapter.get('source_url'),
            'source_site': adapter.get('source_site'),
            'content_type': adapter.get('content_type', 'movie'),
            'metadata': adapter.get('metadata', {}),
        }
        
        # Use get_or_create instead of update_or_create to reduce database locks
        # Atomically get or create/update the Movie
        try:
            movie, created = Movie.objects.update_or_create(
                imdb_id=adapter.get('imdb_id'),
                defaults=movie_defaults
            )
        except Exception as e:
            # If update_or_create fails due to a race condition (IntegrityError),
            # try to just get the existing movie and update it
            if 'unique constraint failed' in str(e).lower():
                movie = Movie.objects.get(imdb_id=adapter.get('imdb_id'))
                # Update existing movie
                for key, value in movie_defaults.items():
                    setattr(movie, key, value)
                movie.save()
                created = False
            else:
                raise

        # Create or update the StreamingLink with server_name
        if adapter.get('stream_url'):
            link_defaults = {
                'server_name': adapter.get('server_name', 'Unknown'),
                'quality': adapter.get('quality', 'SD'),
                'language': adapter.get('language', 'EN'),
                'is_active': True,
                'error_message': '',
                'check_count': 0,
            }
            
            try:
                link = StreamingLink.objects.get(
                    movie=movie,
                    stream_url=adapter.get('stream_url')
                )
                # Update existing link
                for key, value in link_defaults.items():
                    setattr(link, key, value)
                link.save()
                link_created = False
            except StreamingLink.DoesNotExist:
                # Create new link
                link = StreamingLink.objects.create(
                    movie=movie,
                    stream_url=adapter.get('stream_url'),
                    **link_defaults
                )
                link_created = True

            if link_created:
                spider.logger.info(f'✓ Created new {link.server_name} link for {movie.title}')
            else:
                spider.logger.info(f'✓ Updated {link.server_name} link for {movie.title}')

        return adapter.item

    def _log_failed_item(self, adapter, spider):
        """
        Log failed items to a file for manual recovery.
        """
        try:
            import json
            from datetime import datetime
            
            failed_item = {
                'timestamp': datetime.now().isoformat(),
                'imdb_id': adapter.get('imdb_id'),
                'title': adapter.get('title'),
                'year': adapter.get('year'),
                'stream_url': adapter.get('stream_url'),
                'server_name': adapter.get('server_name'),
                'source_url': adapter.get('source_url'),
            }
            
            # Append to failed_items.json
            with open('failed_items.json', 'a') as f:
                f.write(json.dumps(failed_item) + '\n')
                
            spider.logger.info(f'Logged failed item to failed_items.json: {adapter.get("title")}')
        except Exception as e:
            spider.logger.error(f'Failed to log failed item: {e}')
