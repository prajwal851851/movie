import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink

# Get recent Goojara movies
movies = Movie.objects.filter(source_site='goojara.to')[:10]

print(f"\n{'='*60}")
print(f"GOOJARA MOVIES IN DATABASE: {movies.count()}")
print(f"{'='*60}\n")

for movie in movies:
    links = StreamingLink.objects.filter(movie=movie)
    print(f"Title: {movie.title} ({movie.year})")
    print(f"Source: {movie.source_url}")
    if links.exists():
        link = links.first()
        print(f"Stream URL: {link.stream_url}")
        print(f"Quality: {link.quality}")
    else:
        print("Stream URL: No link found")
    print("-" * 60)
