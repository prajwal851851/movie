# streaming/serializers.py
from rest_framework import serializers
from .models import Movie, StreamingLink

class StreamingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingLink
        fields = ['stream_url', 'server_name', 'quality', 'language', 'is_active', 'last_checked']

class MovieSerializer(serializers.ModelSerializer):
    # Show all related streaming links
    links = StreamingLinkSerializer(many=True, read_only=True, source='links.all')

    class Meta:
        model = Movie
        fields = ['imdb_id', 'title', 'year', 'synopsis', 'poster_url', 'source_url', 'source_site', 'links']