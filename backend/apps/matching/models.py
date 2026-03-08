from django.db import models
from django.conf import settings


class Swipe(models.Model):
    ACTION_CHOICES = [('like', 'Like'), ('pass', 'Pass'), ('superlike', 'Superlike')]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swipes_made',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swipes_received',
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_swipe'
        indexes = [
            models.Index(fields=['from_user', 'to_user', 'action']),
        ]
        unique_together = ('from_user', 'to_user')


class Match(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('blocked', 'Bloqué'),
        ('expired', 'Expiré'),
    ]

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matches_as_user1',
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matches_as_user2',
    )
    score_compatibilite = models.IntegerField(default=0)  # 0-100
    raisons_compatibilite = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_match'
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Match {self.user1} ↔ {self.user2} ({self.score_compatibilite}%)"


class PlannedOuting(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'Proposé'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='outings')
    seance = models.ForeignKey('films.Seance', on_delete=models.CASCADE)
    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='outings_proposed',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    meeting_place = models.CharField(max_length=255, blank=True)
    meeting_time = models.DateTimeField(null=True, blank=True)
    proposer_booked = models.BooleanField(default=False)
    partner_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_planned_outing'


class Review(models.Model):
    outing = models.ForeignKey(PlannedOuting, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_review'
        unique_together = ('outing', 'reviewer')
