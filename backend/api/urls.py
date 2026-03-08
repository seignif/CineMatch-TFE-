from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth
    path('auth/', include('apps.users.urls')),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Resources
    path('films/', include('apps.films.urls')),
    path('matching/', include('apps.matching.urls')),
    path('chat/', include('apps.chat.urls')),
]
