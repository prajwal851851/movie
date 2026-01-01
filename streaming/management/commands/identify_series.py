from django.core.management.base import BaseCommand
from streaming.models import Movie
import re


class Command(BaseCommand):
    help = 'Identify and mark series content in the database based on title pattern'

    def handle(self, *args, **options):
        # Pattern to match series episodes like "Title S01, E01" or "Title S26, E1"
        series_pattern = r'S\d+,?\s*E\d+'
        
        updated_count = 0
        movies = Movie.objects.filter(content_type='movie')
        
        for movie in movies:
            if re.search(series_pattern, movie.title):
                movie.content_type = 'series'
                movie.save()
                updated_count += 1
                self.stdout.write(f"Marked as series: {movie.title}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} items as series'))
