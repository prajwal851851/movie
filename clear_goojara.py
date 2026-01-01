import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie

# Delete all Goojara movies
deleted_count = Movie.objects.filter(source_site='goojara.to').delete()
print(f"Deleted {deleted_count[0]} Goojara movies from database")
print("Database cleared. Ready for fresh scrape.")
