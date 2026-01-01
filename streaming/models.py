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
    title = models.CharField(max_length=255, db_index=True)
    year = models.IntegerField(null=True, blank=True, db_index=True)
    synopsis = models.TextField(blank=True)
    poster_url = models.URLField(max_length=1000, blank=True)
    # Store the original page we scraped this from, for re-scraping
    source_url = models.URLField(max_length=1000, blank=True)
    source_site = models.CharField(max_length=50, blank=True, help_text="e.g., makemoviestreaming.com")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='movie', help_text="Movie or Series", db_index=True)
    status = models.CharField(max_length=50, default='Released', db_index=True, help_text="e.g., Released, Upcoming, Post Production")
    metadata = models.JSONField(default=dict, blank=True, help_text="Extra data like season counts e.g. {'seasons': [{'season_number': 1, 'episode_count': 10}]}")
    genre_list = models.CharField(max_length=500, blank=True, db_index=True, help_text="Comma-separated genres for fast filtering")

    def save(self, *args, **kwargs):
        # Automatically populate genre_list from metadata for fast searching
        if self.metadata and isinstance(self.metadata, dict) and 'genres' in self.metadata:
            genres = self.metadata['genres']
            if isinstance(genres, list):
                self.genre_list = ','.join(genres)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.year})"

class StreamingLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='links')
    stream_url = models.URLField(max_length=1000)
    server_name = models.CharField(max_length=50, default='Unknown', help_text="e.g., Dood, Luluvdo, Vidsrc")
    quality = models.CharField(max_length=50, default='Unknown')
    language = models.CharField(max_length=10, default='EN')
    is_active = models.BooleanField(default=True, db_index=True)
    last_checked = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, help_text="Error message if link is broken")
    check_count = models.IntegerField(default=0, help_text="Number of times this link has been checked")

    class Meta:
        unique_together = ('movie', 'stream_url') # Avoid duplicate links

    def __str__(self):
        return f"{self.server_name} link for {self.movie.title}"

from django.conf import settings

class UserWatchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

class UserFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

class WatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    progress = models.FloatField(default=0) # Percentage 0-100
    current_time = models.FloatField(default=0) # Seconds
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-last_watched']

    def __str__(self):
        return f"{self.user.email} watched {self.movie.title}"

class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.email} for {self.movie.title} - {self.rating} stars"
