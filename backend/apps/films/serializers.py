from rest_framework import serializers

from .models import Cinema, Film, Genre, Seance, WatchedFilm


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
                  'audio_language', 'is_special_event', 'min_age']


class FilmDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    seances = SeanceSerializer(many=True, read_only=True)

    class Meta:
        model = Film
        fields = ['id', 'kinepolis_id', 'corporate_id', 'tmdb_id', 'imdb_code',
                  'title', 'synopsis', 'short_synopsis', 'duration', 'release_date',
                  'language', 'audio_language', 'is_future', 'poster_url',
                  'backdrop_url', 'trailer_youtube_key', 'tmdb_rating',
                  'is_special_event', 'min_age', 'genres', 'seances', 'last_sync']


class WatchedFilmSerializer(serializers.ModelSerializer):
    film_info = FilmSerializer(source='film', read_only=True)
    film_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WatchedFilm
        fields = ['id', 'film_id', 'film_info', 'watched_date', 'rating',
                  'review', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicWatchedFilmSerializer(serializers.ModelSerializer):
    """US-064 : Avis public visible par la communauté."""
    author_name = serializers.CharField(source='user.first_name', read_only=True)
    author_picture = serializers.SerializerMethodField()

    class Meta:
        model = WatchedFilm
        fields = ['id', 'author_name', 'author_picture', 'rating',
                  'review', 'watched_date', 'created_at']

    def get_author_picture(self, obj):
        try:
            pic = obj.user.profile.profile_picture
            return pic.url if pic else None
        except Exception:
            return None
