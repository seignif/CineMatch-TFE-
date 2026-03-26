from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Cinema, Film, Seance
from .serializers import (
    CinemaSerializer,
    FilmDetailSerializer,
    FilmSerializer,
    SeanceSerializer,
)


class FilmViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Film.objects.prefetch_related('genres').order_by('-release_date')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FilmDetailSerializer
        return FilmSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        is_future = self.request.query_params.get('is_future')
        if is_future is not None:
            qs = qs.filter(is_future=is_future.lower() in ('true', '1'))
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @action(detail=True, url_path='seances')
    def seances(self, request, pk=None):
        film = self.get_object()
        seances = Seance.objects.filter(film=film).select_related('cinema').order_by('showtime')
        serializer = SeanceSerializer(seances, many=True)
        return Response(serializer.data)


class CinemaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Cinema.objects.filter(is_active=True).order_by('name')
    serializer_class = CinemaSerializer

    @action(detail=True, url_path='seances')
    def seances(self, request, pk=None):
        cinema = self.get_object()
        seances = (
            Seance.objects
            .filter(cinema=cinema)
            .select_related('film')
            .order_by('showtime')
        )
        serializer = SeanceSerializer(seances, many=True)
        return Response(serializer.data)
