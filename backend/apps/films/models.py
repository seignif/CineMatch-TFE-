from django.db import models


class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'films_genre'

    def __str__(self):
        return self.name


class Cinema(models.Model):
    kinepolis_id = models.CharField(max_length=20, unique=True)  # ex: "KBRAI"
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, default='BE')
    language = models.CharField(max_length=5, default='FR')
    is_active = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'films_cinema'

    def __str__(self):
        return self.name


class Film(models.Model):
    kinepolis_id = models.CharField(max_length=50, unique=True)  # ex: "HO00011897"
    corporate_id = models.IntegerField(null=True, blank=True)
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    imdb_code = models.CharField(max_length=20, blank=True)
    title = models.CharField(max_length=255, db_index=True)
    synopsis = models.TextField(blank=True)
    short_synopsis = models.TextField(blank=True)
    duration = models.IntegerField(null=True, blank=True)
    release_date = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=5, default='FR')
    audio_language = models.CharField(max_length=5, blank=True)
    is_future = models.BooleanField(default=False)
    poster_url = models.URLField(blank=True)
    backdrop_url = models.URLField(blank=True)
    trailer_youtube_key = models.CharField(max_length=50, blank=True)
    tmdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'films_film'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_future', '-release_date']),
        ]

    def __str__(self):
        return self.title


class Seance(models.Model):
    kinepolis_session_id = models.CharField(max_length=50, unique=True)  # ex: "KBRAI-208470"
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='seances')
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='seances')
    showtime = models.DateTimeField(db_index=True)
    language = models.CharField(max_length=5, default='FR')
    hall = models.IntegerField(null=True, blank=True)
    vista_session_id = models.IntegerField(null=True, blank=True)
    is_sold_out = models.BooleanField(default=False)
    has_cosy_seating = models.BooleanField(default=False)
    booking_url = models.URLField(blank=True)
    raw_attributes = models.CharField(max_length=100, blank=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'films_seance'
        ordering = ['showtime']
        indexes = [
            models.Index(fields=['film', 'cinema', 'showtime']),
            models.Index(fields=['showtime']),
        ]

    def __str__(self):
        return f"{self.film.title} @ {self.cinema.name} - {self.showtime}"
