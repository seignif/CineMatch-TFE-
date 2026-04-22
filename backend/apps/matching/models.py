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
    ai_generated_reasons = models.JSONField(default=list)
    ai_match_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_match'
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Match {self.user1} ↔ {self.user2} ({self.score_compatibilite}%)"

    def get_other_user(self, user):
        return self.user2 if self.user1 == user else self.user1


class PlannedOuting(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'Proposé'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='outings')
    seance = models.ForeignKey(
        'films.Seance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outings',
    )
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
    proposal_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_planned_outing'
        ordering = ['-created_at']

    def __str__(self):
        film = self.seance.film.title if self.seance else 'film inconnu'
        return f"Sortie {self.match} — {self.status} ({film})"

    def get_partner(self):
        return self.match.get_other_user(self.proposer)

    def is_upcoming(self):
        from django.utils import timezone
        now = timezone.now()
        if self.seance and self.seance.showtime:
            return self.seance.showtime > now
        if self.meeting_time:
            return self.meeting_time > now
        return False


class Review(models.Model):
    """US-038 : Avis post-sortie."""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    outing = models.ForeignKey(PlannedOuting, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
    )
    reviewed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviews_received',
        null=True,
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    would_go_again = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_review'
        unique_together = ('outing', 'reviewer')

    def __str__(self):
        return f"{self.reviewer} → {self.reviewed} ({self.rating}★)"


# ---------------------------------------------------------------------------
# Groupes (US-041 / US-042 / US-043)
# ---------------------------------------------------------------------------

class Group(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('archived', 'Archivé'),
    ]

    name = models.CharField(max_length=100, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='groups_created',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMember',
        through_fields=('group', 'user'),
        related_name='groups_joined',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    chosen_film = models.ForeignKey(
        'films.Film',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chosen_for_groups',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_group'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f"Groupe de {self.creator.first_name}"

    def get_active_members(self):
        return self.members.filter(groupmember__status='accepted')

    def get_active_member_count(self):
        return self.get_active_members().count()


class GroupMember(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Invitation en attente'),
        ('accepted', 'Membre actif'),
        ('declined', 'Invitation refusée'),
    ]
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Membre'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invitations_sent',
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'matching_group_member'
        unique_together = ['group', 'user']

    def __str__(self):
        return f"{self.user.first_name} dans {self.group} ({self.status})"


class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_messages_sent',
    )
    content = models.TextField()
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_group_message'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.first_name}: {self.content[:50]}"


class FilmVote(models.Model):
    VOTE_CHOICES = [('up', '👍'), ('down', '👎')]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='votes')
    film = models.ForeignKey('films.Film', on_delete=models.CASCADE, related_name='group_votes')
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='film_votes',
    )
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matching_film_vote'
        unique_together = ['group', 'film', 'voter']

    def __str__(self):
        return f"{self.voter.first_name} {self.vote} {self.film.title}"
