from rest_framework import serializers
from apps.social.models import Notification, Post, PostComment, PostLike


class PostCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_picture = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'author_id', 'author_name', 'author_picture', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_author_picture(self, obj):
        try:
            pic = obj.author.profile.profile_picture
            return pic.url if pic else None
        except Exception:
            return None


class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_picture = serializers.SerializerMethodField()
    film_info = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    preview_comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author_id', 'author_name', 'author_picture',
            'content', 'film_info',
            'like_count', 'comment_count',
            'is_liked', 'is_author',
            'preview_comments',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_author_picture(self, obj):
        try:
            pic = obj.author.profile.profile_picture
            return pic.url if pic else None
        except Exception:
            return None

    def get_film_info(self, obj):
        if not obj.film:
            return None
        return {
            'id': obj.film.id,
            'title': obj.film.title,
            'poster_url': obj.film.poster_url,
            'kinepolis_id': obj.film.kinepolis_id,
        }

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_author(self, obj):
        request = self.context.get('request')
        return bool(request and obj.author == request.user)

    def get_preview_comments(self, obj):
        comments = obj.comments.select_related('author__profile').order_by('created_at')[:3]
        return PostCommentSerializer(comments, many=True).data


class NotificationSerializer(serializers.ModelSerializer):
    triggered_by_name = serializers.CharField(source='triggered_by.username', read_only=True)
    triggered_by_picture = serializers.SerializerMethodField()
    post_preview = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'message',
            'triggered_by_name', 'triggered_by_picture',
            'post_preview', 'is_read', 'created_at',
        ]

    def get_triggered_by_picture(self, obj):
        try:
            if obj.triggered_by:
                pic = obj.triggered_by.profile.profile_picture
                return pic.url if pic else None
        except Exception:
            pass
        return None

    def get_post_preview(self, obj):
        if obj.post:
            return {'id': obj.post.id, 'content': obj.post.content[:100]}
        return None
