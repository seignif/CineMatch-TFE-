import uuid as _uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone as _tz


MOOD_CHOICES = [
    ('rire', 'Envie de rire'),
    ('reflechir', 'Besoin de reflechir'),
    ('emu', "Envie d'etre emu"),
    ('adrenaline', "Besoin d'adrenaline"),
]

LANGUAGE_PREF_CHOICES = [
    ('vf', 'Version Française (VF)'),
    ('vo', 'Version Originale (VO/VOST)'),
    ('both', 'Les deux'),
]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_email_verified = models.BooleanField(default=False)
    cgu_accepted_at = models.DateTimeField(null=True, blank=True)

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
    language_preference = models.CharField(
        max_length=10, choices=LANGUAGE_PREF_CHOICES, default='both'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    search_radius_km = models.IntegerField(default=15)
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


class EmailVerificationToken(models.Model):
    """US-065 : Token de vérification email (UUID, valide 24h)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_token',
    )
    token = models.UUIDField(default=_uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'users_email_verification_token'

    def is_valid(self):
        return _tz.now() < self.expires_at

    def __str__(self):
        return f"Token {self.user.email}"
