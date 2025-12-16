# streaming/serializers.py
from rest_framework import serializers
from .models import Movie, StreamingLink

class StreamingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingLink
        fields = ('stream_url', 'quality', 'language', 'is_active')

class MovieSerializer(serializers.ModelSerializer):
    # This will show the related streaming links for each movie
    links = StreamingLinkSerializer(source='links.all', many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ('imdb_id', 'title', 'year', 'synopsis', 'poster_url', 'source_site', 'links')