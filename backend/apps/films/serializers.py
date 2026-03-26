from rest_framework import serializers

from .models import Cinema, Film, Genre, Seance


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'tmdb_id']


class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ['id', 'kinepolis_id', 'name', 'country', 'language', 'is_active',
                  'latitude', 'longitude']


class SeanceSerializer(serializers.ModelSerializer):
    cinema = CinemaSerializer(read_only=True)

    class Meta:
        model = Seance
        fields = ['id', 'kinepolis_session_id', 'cinema', 'showtime', 'language',
                  'hall', 'is_sold_out', 'has_cosy_seating', 'booking_url',
                  'raw_attributes']


class FilmSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Film
        fields = ['id', 'kinepolis_id', 'title', 'poster_url', 'duration',
                  'release_date', 'is_future', 'genres', 'tmdb_rating',
                  'audio_language']


class FilmDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    seances = SeanceSerializer(many=True, read_only=True)

    class Meta:
        model = Film
        fields = ['id', 'kinepolis_id', 'corporate_id', 'tmdb_id', 'imdb_code',
                  'title', 'synopsis', 'short_synopsis', 'duration', 'release_date',
                  'language', 'audio_language', 'is_future', 'poster_url',
                  'backdrop_url', 'trailer_youtube_key', 'tmdb_rating',
                  'genres', 'seances', 'last_sync']
