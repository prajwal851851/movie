# scraper/scraper/pipelines.py
from itemadapter import ItemAdapter
from streaming.models import Movie, StreamingLink
from twisted.internet import threads

class DjangoItemPipeline:
    def process_item(self, item, spider):
        # Use Twisted's deferToThread to run Django ORM in a separate thread
        return threads.deferToThread(self._process_item_sync, item, spider)
    
    def _process_item_sync(self, item, spider):
        """Synchronous processing of item in a separate thread"""
        adapter = ItemAdapter(item)

        # Create or update the Movie
        movie_defaults = {
            'title': adapter.get('title'),
            'year': adapter.get('year'),
            'synopsis': adapter.get('synopsis'),
            'poster_url': adapter.get('poster_url'),
            'source_url': adapter.get('source_url'),
            'source_site': adapter.get('source_site'),
        }
        movie, created = Movie.objects.update_or_create(
            imdb_id=adapter.get('imdb_id'),
            defaults=movie_defaults
        )

        # Create or update the StreamingLink with server_name
        if adapter.get('stream_url'):
            link_defaults = {
                'server_name': adapter.get('server_name', 'Unknown'),
                'quality': adapter.get('quality'),
                'language': adapter.get('language'),
                'is_active': True,
                'error_message': '',
                'check_count': 0,
            }
            link, link_created = StreamingLink.objects.update_or_create(
                movie=movie,
                stream_url=adapter.get('stream_url'),
                defaults=link_defaults
            )
            
            if link_created:
                spider.logger.info(f'Created new {link.server_name} link for {movie.title}')
            else:
                spider.logger.info(f'Updated {link.server_name} link for {movie.title}')
        
        return item