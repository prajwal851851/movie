from django.db import models

# Create your models here.
# streaming/models.py
from django.db import models

class Movie(models.Model):
    CONTENT_TYPES = [
        ('movie', 'Movie'),
        ('series', 'Series'),
    ]
    
    imdb_id = models.CharField(max_length=20, unique=True, primary_key=True, help_text="e.g., tt0468569")
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    synopsis = models.TextField(blank=True)
    poster_url = models.URLField(max_length=1000, blank=True)
    # Store the original page we scraped this from, for re-scraping
    source_url = models.URLField(max_length=1000, blank=True)
    source_site = models.CharField(max_length=50, blank=True, help_text="e.g., makemoviestreaming.com")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='movie', help_text="Movie or Series")

    def __str__(self):
        return f"{self.title} ({self.year})"

class StreamingLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='links')
    stream_url = models.URLField(max_length=1000)
    server_name = models.CharField(max_length=50, default='Unknown', help_text="e.g., Dood, Luluvdo, Vidsrc")
    quality = models.CharField(max_length=50, default='Unknown')
    language = models.CharField(max_length=10, default='EN')
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, help_text="Error message if link is broken")
    check_count = models.IntegerField(default=0, help_text="Number of times this link has been checked")

    class Meta:
        unique_together = ('movie', 'stream_url') # Avoid duplicate links

    def __str__(self):
        return f"{self.server_name} link for {self.movie.title}"