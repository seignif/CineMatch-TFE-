import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings
from django.db import models as db_models
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Cinema, Film, Seance, WatchedFilm
from .serializers import (
    CinemaSerializer,
    FilmDetailSerializer,
    FilmSerializer,
    PublicWatchedFilmSerializer,
    SeanceSerializer,
    WatchedFilmSerializer,
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
        params = self.request.query_params

        # Masquer événements spéciaux par défaut (opéras, concerts…)
        show_events = params.get('show_events', 'false')
        if show_events != 'true':
            qs = qs.filter(is_special_event=False)

        is_future = params.get('is_future')
        if is_future is not None:
            qs = qs.filter(is_future=is_future.lower() in ('true', '1'))

        search = params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)

        genre = params.get('genre')
        if genre:
            qs = qs.filter(genres__name__iexact=genre)

        min_rating = params.get('min_rating')
        if min_rating:
            try:
                qs = qs.filter(tmdb_rating__gte=float(min_rating))
            except ValueError:
                pass

        max_age = params.get('max_age')
        if max_age:
            try:
                qs = qs.filter(
                    db_models.Q(min_age__lte=int(max_age)) |
                    db_models.Q(min_age__isnull=True)
                )
            except ValueError:
                pass

        is_future_param = params.get('is_future')
        qs = qs.distinct()

        if is_future_param is not None:
            if is_future_param.lower() in ('true', '1'):
                # Bientôt : tri par date de sortie croissante
                return qs.order_by('release_date')
            else:
                # À l'affiche : masquer les films sans séance à venir
                return qs.filter(seances__showtime__gte=timezone.now()).distinct()

        return qs

    @action(detail=False, url_path='genres', permission_classes=[AllowAny])
    def genres(self, request):
        from apps.films.models import Genre
        genres = Genre.objects.filter(film__isnull=False).values_list('name', flat=True).distinct().order_by('name')
        return Response(list(genres))

    @action(detail=True, url_path='seances')
    def seances(self, request, pk=None):
        film = self.get_object()
        seances = (
            Seance.objects
            .filter(film=film, showtime__gte=timezone.now())
            .select_related('cinema')
            .order_by('showtime')
        )
        cinema_id = request.query_params.get('cinema')
        if cinema_id:
            seances = seances.filter(cinema__kinepolis_id=cinema_id)

        lang_filter = request.query_params.get('language')
        if lang_filter == 'vf':
            seances = seances.filter(language__in=['FR', 'NL'])
        elif lang_filter == 'vo':
            seances = seances.exclude(language__in=['FR', 'NL'])

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
            # Chercher d'abord par tmdb_id (film Kinepolis déjà enrichi)
            # puis par kinepolis_id tmdb_ (film signature déjà créé)
            # sinon créer
            film = (
                Film.objects.filter(tmdb_id=tmdb_id).first()
                or Film.objects.filter(kinepolis_id=f'tmdb_{tmdb_id}').first()
            )
            if film is None:
                film = Film.objects.create(
                    kinepolis_id=f'tmdb_{tmdb_id}',
                    title=item.get('title', ''),
                    tmdb_id=tmdb_id,
                    poster_url=poster,
                    synopsis=item.get('overview', ''),
                    release_date=item.get('release_date') or None,
                )
                # Assigner les genres depuis TMDb genre_ids
                from .models import Genre
                genre_ids = item.get('genre_ids', [])
                if genre_ids:
                    genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                    if genres.exists():
                        film.genres.set(genres)
            elif not film.genres.exists():
                # Film existant sans genres → essayer d'assigner
                from .models import Genre
                genre_ids = item.get('genre_ids', [])
                if genre_ids:
                    genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                    if genres.exists():
                        film.genres.set(genres)
            results.append(FilmSerializer(film).data)

        return Response(results)


class WatchedFilmViewSet(viewsets.ModelViewSet):
    """US-063 : Journal personnel de films vus."""
    permission_classes = [IsAuthenticated]
    serializer_class = WatchedFilmSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return WatchedFilm.objects.filter(
            user=self.request.user
        ).select_related('film').prefetch_related('film__genres')

    def perform_create(self, serializer):
        from .models import Film as FilmModel
        film_id = self.request.data.get('film_id')
        film = FilmModel.objects.get(id=film_id)
        serializer.save(user=self.request.user, film=film)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.db.models import Avg
        from apps.films.models import Genre
        qs = WatchedFilm.objects.filter(user=request.user)
        total = qs.count()
        avg_rating = qs.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
        top_genre = (
            Genre.objects
            .filter(film__watched_by__user=request.user)
            .annotate(count=db_models.Count('id'))
            .order_by('-count')
            .first()
        )
        return Response({
            'total_watched': total,
            'average_rating': round(avg_rating, 1) if avg_rating else None,
            'top_genre': top_genre.name if top_genre else None,
        })


class FilmReviewsView(generics.ListAPIView):
    """US-064 : Avis publics sur un film."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PublicWatchedFilmSerializer

    def get_queryset(self):
        return WatchedFilm.objects.filter(
            film_id=self.kwargs['pk'],
            is_public=True,
            rating__isnull=False,
        ).select_related('user__profile').order_by('-created_at')


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
