from rest_framework import generics, status, permissions
from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from apps.social.models import Notification, Post, PostComment, PostLike, Report
from apps.social.serializers import (
    NotificationSerializer, PostCommentSerializer, PostSerializer,
)


class PostListCreateView(generics.ListCreateAPIView):
    """US-067/068 : Feed + création de posts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        qs = Post.objects.filter(is_hidden=False).select_related(
            'author__profile', 'film'
        ).prefetch_related(
            'likes', 'comments__author__profile'
        ).order_by('-created_at')

        film_id = self.request.query_params.get('film_id')
        if film_id:
            qs = qs.filter(film_id=film_id)

        matches_only = self.request.query_params.get('matches_only')
        if matches_only:
            from apps.matching.models import Match
            user = self.request.user
            matched_pairs = Match.objects.filter(
                Q(user1=user) | Q(user2=user), status='active'
            ).values_list('user1_id', 'user2_id')
            match_user_ids = set()
            for u1, u2 in matched_pairs:
                match_user_ids.add(u1)
                match_user_ids.add(u2)
            match_user_ids.discard(user.id)
            qs = qs.filter(author_id__in=match_user_ids)

        return qs

    def perform_create(self, serializer):
        film_id = self.request.data.get('film_id')
        film = None
        if film_id:
            from apps.films.models import Film
            film = Film.objects.filter(id=film_id).first()
        serializer.save(author=self.request.user, film=film)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class PostDetailView(generics.RetrieveDestroyAPIView):
    """GET/DELETE /api/social/posts/:id/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    queryset = Post.objects.select_related('author__profile', 'film').prefetch_related(
        'likes', 'comments__author__profile'
    )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {"error": "Vous ne pouvez supprimer que vos propres posts."},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostLikeView(APIView):
    """US-069 : Toggle like — POST /api/social/posts/:id/like/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(id=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post introuvable."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        existing = PostLike.objects.filter(post=post, user=user).first()

        if existing:
            existing.delete()
            liked = False
        else:
            PostLike.objects.create(post=post, user=user)
            liked = True
            if post.author != user:
                Notification.objects.get_or_create(
                    user=post.author,
                    type='like_post',
                    post=post,
                    triggered_by=user,
                    defaults={'message': f"{user.first_name} a aimé votre post."},
                )

        return Response({"liked": liked, "like_count": post.likes.count()})


class PostCommentListCreateView(generics.ListCreateAPIView):
    """US-070 : GET/POST /api/social/posts/:id/comments/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostCommentSerializer

    def get_queryset(self):
        return PostComment.objects.filter(
            post_id=self.kwargs['pk']
        ).select_related('author__profile').order_by('created_at')

    def perform_create(self, serializer):
        try:
            post = Post.objects.get(id=self.kwargs['pk'])
        except Post.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Post introuvable.")

        comment = serializer.save(author=self.request.user, post=post)

        if post.author != self.request.user:
            Notification.objects.create(
                user=post.author,
                type='comment_post',
                post=post,
                triggered_by=self.request.user,
                message=(
                    f"{self.request.user.first_name} a commenté votre post : "
                    f'"{comment.content[:50]}"'
                ),
            )


class PostCommentDeleteView(generics.DestroyAPIView):
    """DELETE /api/social/comments/:id/"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PostComment.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(
                {"error": "Vous ne pouvez supprimer que vos commentaires."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListView(generics.ListAPIView):
    """US-072 : GET /api/social/notifications/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('triggered_by__profile', 'post').order_by('-created_at')[:50]


class NotificationMarkReadView(APIView):
    """POST /api/social/notifications/read/ ou /api/social/notifications/:id/read/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(id=pk, user=request.user).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "Notifications marquées comme lues."})


class UnreadNotificationCountView(APIView):
    """GET /api/social/notifications/unread-count/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})


class ReportSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'type', 'reason', 'description',
            'post', 'comment', 'message_id',
            'message_content', 'reported_user',
        ]


class ReportCreateView(generics.CreateAPIView):
    """US-075/076 : Signaler un contenu — POST /api/social/reports/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        # Empêcher de se signaler soi-même
        reported_user_id = request.data.get('reported_user')
        if reported_user_id and str(reported_user_id) == str(request.user.id):
            return Response(
                {"error": "Vous ne pouvez pas vous signaler vous-même."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Empêcher les doublons
        existing = Report.objects.filter(
            reporter=request.user,
            post_id=request.data.get('post') or None,
            message_id=request.data.get('message_id') or None,
            status='pending',
        ).first()
        if existing:
            return Response(
                {"message": "Vous avez déjà signalé ce contenu."},
                status=status.HTTP_200_OK,
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        report = serializer.save(reporter=self.request.user)

        # Auto-masquer le post si 3 signalements pending
        if report.post:
            count = Report.objects.filter(post=report.post, status='pending').count()
            if count >= 3:
                report.post.is_hidden = True
                report.post.save(update_fields=['is_hidden'])
