from django.urls import include, path

urlpatterns = [
    # Auth + Users (users/urls.py contient les préfixes auth/ et users/)
    path('', include('apps.users.urls')),
    # Ressources
    path('films/', include('apps.films.urls')),
    path('matching/', include('apps.matching.urls')),
    path('chat/', include('apps.chat.urls')),
]
