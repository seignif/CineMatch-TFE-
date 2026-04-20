from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users import views

urlpatterns = [
    # Authentification
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Profil utilisateur
    path('users/me/', views.MeView.as_view(), name='me'),
    path('users/me/profile/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('users/me/picture/', views.UploadProfilePictureView.as_view(), name='upload_picture'),

    # Badges, réputation, recommandations (US-035/039/040)
    path('users/badges/', views.BadgesView.as_view(), name='badges'),
    path('users/reputation/<int:pk>/', views.ReputationView.as_view(), name='reputation'),
    path('users/recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
]
