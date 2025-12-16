from django.db import models

# Create your models here.
# streaming/models.py
from django.db import models

class Movie(models.Model):
    imdb_id = models.CharField(max_length=20, unique=True, primary_key=True, help_text="e.g., tt0468569")
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    synopsis = models.TextField(blank=True)
    poster_url = models.URLField(max_length=1000, blank=True)
    # Store the original page we scraped this from, for re-scraping
    source_url = models.URLField(max_length=1000, blank=True)
    source_site = models.CharField(max_length=50, blank=True, help_text="e.g., makemoviestreaming.com")

    def __str__(self):
        return f"{self.title} ({self.year})"

class StreamingLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='links')
    stream_url = models.URLField(max_length=1000)
    quality = models.CharField(max_length=50, default='Unknown')
    language = models.CharField(max_length=10, default='EN')
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('movie', 'stream_url') # Avoid duplicate links

    def __str__(self):
        return f"Link for {self.movie.title}"