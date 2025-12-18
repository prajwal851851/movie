import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink

# Delete all 123movies.com movies
movies = Movie.objects.filter(source_site='123movies.com')
count = movies.count()
movies.delete()

print(f'Deleted {count} 123movies.com movies from database')
