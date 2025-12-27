import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

from streaming.models import Movie

# Check sflix movies
sflix_movies = Movie.objects.filter(source_site__icontains='sflix')[:10]

print(f'Total sflix movies: {Movie.objects.filter(source_site__icontains="sflix").count()}')
print('\nSample sflix movies:')
for m in sflix_movies:
    print(f'  - {m.title}')
    print(f'    poster_url: {m.poster_url or "NONE"}')
    print(f'    year: {m.year}')
    print(f'    source_site: {m.source_site}')
    print()
