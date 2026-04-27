from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CinemaViewSet, FilmReviewsView, FilmViewSet, WatchedFilmViewSet

router = DefaultRouter()
router.register('films', FilmViewSet, basename='film')
router.register('cinemas', CinemaViewSet, basename='cinema')
router.register('watched', WatchedFilmViewSet, basename='watched')

urlpatterns = [
    path('', include(router.urls)),
    path('films/<int:pk>/reviews/', FilmReviewsView.as_view(), name='film-reviews'),
]
