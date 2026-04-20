import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    queryset = (
        Film.objects
        .exclude(kinepolis_id__startswith='tmdb_')
        .prefetch_related('genres')
        .order_by('-release_date')
    )

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

    @action(detail=False, url_path='tmdb-search', permission_classes=[IsAuthenticated])
    def tmdb_search(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response([])

        api_key = getattr(settings, 'TMDB_API_KEY', '')
        if not api_key:
            return Response([])

        session = requests.Session()
        session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.3)))

        resp = session.get(
            'https://api.themoviedb.org/3/search/movie',
            params={'api_key': api_key, 'query': q, 'language': 'fr-FR', 'page': 1},
            timeout=8,
        )
        if resp.status_code != 200:
            return Response([])

        results = []
        for item in resp.json().get('results', [])[:10]:
            tmdb_id = item['id']
            poster = f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get('poster_path') else ''
            film, _ = Film.objects.get_or_create(
                kinepolis_id=f'tmdb_{tmdb_id}',
                defaults={
                    'title': item.get('title', ''),
                    'tmdb_id': tmdb_id,
                    'poster_url': poster,
                    'synopsis': item.get('overview', ''),
                    'release_date': item.get('release_date') or None,
                },
            )
            results.append(FilmSerializer(film).data)

        return Response(results)


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
