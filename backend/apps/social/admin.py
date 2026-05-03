from django.contrib import admin
from apps.social.models import Notification, Post, PostComment, PostLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_preview', 'film', 'like_count', 'comment_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__email', 'content']
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Contenu'

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'

    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Commentaires'


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content', 'created_at']
    ordering = ['-created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'triggered_by', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
    ordering = ['-created_at']
