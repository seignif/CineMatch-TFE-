from django.contrib.auth.models import AbstractUser
from django.db import models


MOOD_CHOICES = [
    ('rire', 'Envie de rire'),
    ('reflechir', 'Besoin de reflechir'),
    ('emu', "Envie d'etre emu"),
    ('adrenaline', "Besoin d'adrenaline"),
]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users_user'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True)
    genre_preferences = models.JSONField(default=dict)
    films_signature = models.ManyToManyField(
        'films.Film',
        through='ProfileFilmSignature',
        blank=True,
    )
    badges = models.JSONField(default=list)
    stats = models.JSONField(default=dict)
    rgpd_consent = models.BooleanField(default=False)
    rgpd_consent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_profile'

    def __str__(self):
        return f"Profil de {self.user.email}"


class ProfileFilmSignature(models.Model):
    """Films signature de l'utilisateur (max 5)."""
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    film = models.ForeignKey('films.Film', on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_profile_film_signature'
        ordering = ['order']
        unique_together = ('profile', 'film')
