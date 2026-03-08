from django.db import models


class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    nom = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'films_genre'

    def __str__(self):
        return self.nom


class Film(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    titre = models.CharField(max_length=255, db_index=True)
    titre_original = models.CharField(max_length=255)
    synopsis = models.TextField(blank=True)
    poster = models.URLField(blank=True)
    backdrop = models.URLField(blank=True)
    trailer_youtube_key = models.CharField(max_length=50, blank=True)
    duree = models.IntegerField(null=True, blank=True)  # minutes
    date_sortie = models.DateField(null=True, blank=True)
    note = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    vote_count = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, blank=True)
    is_now_playing = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'films_film'
        indexes = [
            models.Index(fields=['titre']),
            models.Index(fields=['is_now_playing', '-date_sortie']),
        ]

    def __str__(self):
        return self.titre


class CinemaChain(models.Model):
    allocine_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    logo = models.URLField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        db_table = 'films_cinema_chain'

    def __str__(self):
        return self.name


class Cinema(models.Model):
    allocine_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    chain = models.ForeignKey(CinemaChain, null=True, blank=True, on_delete=models.SET_NULL)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=2, default='BE')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'films_cinema'
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Seance(models.Model):
    VERSION_CHOICES = [('VF', 'VF'), ('VO', 'VO'), ('VOST', 'VOST')]
    FORMAT_CHOICES = [('2D', '2D'), ('3D', '3D'), ('IMAX', 'IMAX'), ('4DX', '4DX')]

    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='seances')
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='seances')
    date_heure = models.DateTimeField(db_index=True)
    version = models.CharField(max_length=4, choices=VERSION_CHOICES, default='VF')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='2D')
    places_restantes = models.IntegerField(null=True, blank=True)
    booking_url = models.URLField(blank=True)

    class Meta:
        db_table = 'films_seance'
        indexes = [
            models.Index(fields=['film', 'cinema', 'date_heure']),
            models.Index(fields=['date_heure']),
        ]
        unique_together = ('film', 'cinema', 'date_heure', 'version', 'format')

    def __str__(self):
        return f"{self.film.titre} @ {self.cinema.name} - {self.date_heure}"
