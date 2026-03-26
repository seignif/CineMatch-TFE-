from django.contrib.auth import get_user_model
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

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": f"Bienvenue {user.first_name} ! Compte créé avec succès.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
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
