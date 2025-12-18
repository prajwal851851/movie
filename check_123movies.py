import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink

movies = Movie.objects.filter(source_site='123movies.com')
print(f'\n123MOVIES COUNT: {movies.count()}\n')

for m in movies[:5]:
    links = StreamingLink.objects.filter(movie=m)
    stream_url = links.first().stream_url if links.exists() else 'No stream'
    print(f'Title: {m.title}')
    print(f'Stream: {stream_url}')
    print('---')
