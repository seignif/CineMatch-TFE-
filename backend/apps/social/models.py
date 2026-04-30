from django.db import models
from django.conf import settings


class Post(models.Model):
    """US-067 : Post dans L'Entracte."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    film = models.ForeignKey(
        'films.Film',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts',
    )
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['film', '-created_at']),
        ]

    def __str__(self):
        return f"{self.author.first_name}: {self.content[:50]}"

    def get_like_count(self):
        return self.likes.count()

    def get_comment_count(self):
        return self.comments.count()


class PostLike(models.Model):
    """US-069 : Like sur un post."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f"{self.user.first_name} liked {self.post}"


class PostComment(models.Model):
    """US-070 : Commentaire sur un post."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_comments',
    )
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.first_name}: {self.content[:50]}"


class Notification(models.Model):
    """US-072 : Notifications sociales."""
    TYPE_CHOICES = [
        ('like_post', 'Like sur votre post'),
        ('comment_post', 'Commentaire sur votre post'),
        ('new_match', 'Nouveau match'),
        ('group_invitation', 'Invitation a un groupe'),
        ('outing_confirmed', 'Sortie confirmee'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications',
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications_triggered',
    )
    message = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.first_name} — {self.type}"
