from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CinemaViewSet, FilmViewSet

router = DefaultRouter()
router.register('films', FilmViewSet, basename='film')
router.register('cinemas', CinemaViewSet, basename='cinema')

urlpatterns = [
    path('', include(router.urls)),
]
