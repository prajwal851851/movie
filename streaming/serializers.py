# streaming/serializers.py
from rest_framework import serializers
from .models import Movie, StreamingLink, UserWatchlist, UserFavorite, WatchHistory, Review

class StreamingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingLink
        fields = ['stream_url', 'server_name', 'quality', 'language', 'is_active', 'last_checked']

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'movie', 'user', 'user_email', 'user_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user']

class MovieSerializer(serializers.ModelSerializer):
    # Show all related streaming links
    links = StreamingLinkSerializer(many=True, read_only=True, source='links.all')
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['imdb_id', 'title', 'year', 'synopsis', 'poster_url', 'source_url', 'source_site', 'content_type', 'metadata', 'links', 'reviews', 'average_rating']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)

class UserWatchlistSerializer(serializers.ModelSerializer):
    movie_details = MovieSerializer(source='movie', read_only=True)
    
    class Meta:
        model = UserWatchlist
        fields = ['id', 'movie', 'movie_details', 'added_at']

class UserFavoriteSerializer(serializers.ModelSerializer):
    movie_details = MovieSerializer(source='movie', read_only=True)

    class Meta:
        model = UserFavorite
        fields = ['id', 'movie', 'movie_details', 'added_at']

class WatchHistorySerializer(serializers.ModelSerializer):
    movie_details = MovieSerializer(source='movie', read_only=True)

    class Meta:
        model = WatchHistory
        fields = ['id', 'movie', 'movie_details', 'progress', 'current_time', 'season', 'episode', 'last_watched']
