import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink

# Check total movies
total_movies = Movie.objects.count()
goojara_movies = Movie.objects.filter(source_site='goojara.to').count()

print(f'Total movies in database: {total_movies}')
print(f'Goojara movies: {goojara_movies}')

# Show recent Goojara movies
print('\n=== Recent Goojara Movies ===')
recent_goojara = Movie.objects.filter(source_site='goojara.to')[:15]
for movie in recent_goojara:
    links_count = movie.links.count()
    print(f'  - {movie.title} ({movie.year}) - {links_count} link(s)')
    if links_count > 0:
        for link in movie.links.all()[:2]:
            print(f'    → {link.stream_url[:80]}...')

# Check all sources
print('\n=== Movies by Source ===')
from django.db.models import Count
sources = Movie.objects.values('source_site').annotate(count=Count('imdb_id')).order_by('-count')
for source in sources:
    print(f'  - {source["source_site"]}: {source["count"]} movies')
