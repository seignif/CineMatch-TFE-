import json
import uuid as _uuid

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """US-004 : Inscription utilisateur."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # US-065 : email de vérification (non bloquant)
        try:
            from apps.users.email_service import EmailService
            EmailService.send_verification_email(user)
            email_sent = True
        except Exception:
            email_sent = False

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": f"Bienvenue {user.first_name} ! Compte créé avec succès.",
                "email_verification_sent": email_sent,
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """GET /api/auth/verify-email/<token>/ — US-065."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        from apps.users.email_service import EmailService
        success, message = EmailService.verify_token(str(token))
        if success:
            return Response({"message": message})
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """POST /api/auth/resend-verification/ — US-065."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_email_verified:
            return Response({"message": "Email déjà vérifié."})
        try:
            from apps.users.email_service import EmailService
            EmailService.send_verification_email(user)
            return Response({"message": "Email de vérification renvoyé !"})
        except Exception:
            return Response(
                {"error": "Erreur lors de l'envoi. Réessayez plus tard."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutView(APIView):
    """US-006 : Déconnexion (blacklist le refresh token)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response(
                {"message": "Vous êtes déconnecté."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": "Token invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(generics.RetrieveUpdateAPIView):
    """GET / PATCH infos de base de l'utilisateur connecté."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UpdateProfileView(generics.UpdateAPIView):
    """US-008 : Modifier le profil cinématographique."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    def get_object(self):
        return self.request.user.profile


class UploadProfilePictureView(APIView):
    """Upload de la photo de profil."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'picture' not in request.FILES:
            return Response(
                {"error": "Aucune image fournie."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = request.user.profile
        profile.profile_picture = request.FILES['picture']
        profile.save()
        return Response(
            {"message": "Photo mise à jour.", "url": profile.profile_picture.url},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """US-007 : Changement de mot de passe."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Ancien mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            {"message": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK,
        )


class BadgesView(APIView):
    """GET /api/users/badges/ — Liste tous les badges (US-039)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.users.badge_service import BadgeService
        badges = BadgeService.get_all_badges_info(request.user)
        return Response({'badges': badges})


class ReputationView(APIView):
    """GET /api/users/reputation/<id>/ — Score de réputation public (US-040)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from apps.users.badge_service import BadgeService
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)
        return Response(BadgeService.get_reputation_score(target))


class RecommendationsView(APIView):
    """GET /api/users/recommendations/ — Films recommandés personnalisés (US-035)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from apps.films.services.recommendation_service import RecommendationService
        from apps.films.serializers import FilmSerializer

        user = request.user if request.user.is_authenticated else None
        recs = RecommendationService().get_recommendations(user, limit=5)
        data = [
            {
                'film': FilmSerializer(r['film'], context={'request': request}).data,
                'score': r['score'],
                'reasons': r['reasons'],
            }
            for r in recs
        ]
        return Response(data)


class ExportDataView(APIView):
    """US-059 : Export RGPD — GET /api/users/export-data/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        from apps.matching.models import Match, PlannedOuting, Review
        from apps.chat.models import Message
        from apps.social.models import Post, PostComment
        from apps.films.models import WatchedFilm
        from django.db.models import Q

        profile = {}
        try:
            p = user.profile
            profile = {
                'bio': p.bio,
                'mood': p.mood,
                'language_preference': p.language_preference,
                'genre_preferences': p.genre_preferences,
                'badges': p.badges,
                'search_radius_km': p.search_radius_km,
            }
        except Exception:
            pass

        def serialize_dates(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        data = {
            'export_date': timezone.now().isoformat(),
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'city': user.city,
                'date_joined': user.date_joined.isoformat(),
                'is_email_verified': user.is_email_verified,
                'cgu_accepted_at': user.cgu_accepted_at.isoformat() if user.cgu_accepted_at else None,
            },
            'profile': profile,
            'matches': list(
                Match.objects.filter(Q(user1=user) | Q(user2=user))
                .values('created_at', 'status', 'score_compatibilite')
            ),
            'messages_sent': list(
                Message.objects.filter(sender=user).values('content', 'created_at')
            ),
            'outings': list(
                PlannedOuting.objects.filter(
                    Q(proposer=user) | Q(match__user1=user) | Q(match__user2=user)
                ).values('status', 'created_at', 'meeting_place')
            ),
            'reviews_given': list(
                Review.objects.filter(reviewer=user)
                .values('rating', 'would_go_again', 'comment', 'created_at')
            ),
            'posts': list(
                Post.objects.filter(author=user).values('content', 'created_at')
            ),
            'comments': list(
                PostComment.objects.filter(author=user).values('content', 'created_at')
            ),
            'journal': list(
                WatchedFilm.objects.filter(user=user)
                .values('film__title', 'rating', 'review', 'watched_date')
            ),
        }

        json_data = json.dumps(data, default=serialize_dates, ensure_ascii=False, indent=2)

        try:
            from apps.users.email_service import EmailService
            EmailService.send_export_confirmation(user)
        except Exception:
            pass

        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="cinematch_data_{user.id}.json"'
        return response


class DeleteAccountView(APIView):
    """US-060 : Suppression de compte RGPD — POST /api/users/delete-account/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get('password', '')

        if not user.check_password(password):
            return Response(
                {"error": "Mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = user.email
        first_name = user.first_name

        # Envoyer l'email avant de modifier l'adresse
        try:
            from apps.users.email_service import EmailService
            EmailService.send_deletion_confirmation(email, first_name)
        except Exception:
            pass

        # Blacklist le refresh token si fourni
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        # Anonymiser puis désactiver
        self._anonymize_user(user)

        return Response({"message": "Compte supprimé. Vos données personnelles seront effacées dans 30 jours."})

    def _anonymize_user(self, user):
        try:
            profile = user.profile
            profile.bio = ''
            profile.profile_picture = None
            profile.genre_preferences = {}
            profile.badges = []
            profile.latitude = None
            profile.longitude = None
            profile.save()
        except Exception:
            pass

        anon_id = str(_uuid.uuid4())[:8]
        user.email = f"deleted_{anon_id}@cinematch.deleted"
        user.first_name = "Utilisateur"
        user.last_name = "supprimé"
        user.username = f"deleted_{anon_id}"
        user.is_active = False
        user.save()
