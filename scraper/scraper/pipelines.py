# scraper/scraper/pipelines.py
from itemadapter import ItemAdapter
from streaming.models import Movie, StreamingLink

class DjangoItemPipeline:
    def process_item(self, item, spider):
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

        # Create or update the StreamingLink
        if adapter.get('stream_url'):
            link_defaults = {
                'quality': adapter.get('quality'),
                'language': adapter.get('language'),
            }
            StreamingLink.objects.update_or_create(
                movie=movie,
                stream_url=adapter.get('stream_url'),
                defaults=link_defaults
            )
        return item